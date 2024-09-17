def kw(value: str | int | float) -> float:
    return float(value) * 1000


def watt(value: str | int | float) -> float:
    return float(value)


class House:
    def __init__(self) -> None:
        self.INVERTER_MAX = kw(2.67)
        self.SOLAR_MAX = kw(3.67)

        self.solar_power = kw(sensor.foxess_solar_power)
        self.load_power = kw(sensor.foxess_load_power)
        self.grid_consumption = watt(
            sensor.octopus_energy_electricity_23l3042499_2700008005722_current_demand
        )
        self.battery_charge = float(sensor.foxess_bat_soc)


class Options:
    def __init__(self) -> None:
        self.charge_type = input_select.car_charging
        self.battery_min = 30


class Charger:
    def __init__(self) -> None:
        self.CHARGE_VOLTS = 230
        self.house_id = "e658d337f118a91c07ecc90b1482f639"  # move to state
        self.charger_id = "78ca94b33412b017cf3b53429b9a0b49"  # move to state
        self.load_power = kw(max(0, float(sensor.car_charging_kw)))
        log.warning("load power:" + str(self.load_power))
        self.available_current = float(
            state.get("number.28_oriel_road_available_current")
        )

    def to_current(self, power: float) -> float:
        return watt(power) / self.CHARGE_VOLTS

    def set_power_limit(self, new_load_power: float) -> None:

        current = self.to_current(new_load_power)
        if current < 6:
            self.set_current_limit(0)
            self.switch_charger("off")
            return ""
        elif self.available_current != current:
            self.set_current_limit(current)
        self.switch_charger("on")

    def set_current_limit(self, current: float) -> None:
        log.warning(f"limit current: {int(current)}")
        zaptec.limit_current(
            blocking=False,
            return_response=False,
            device_id=self.house_id,
            available_current=int(current),
        )

    def switch_charger(self, on_off: str) -> None:
        switch.charger_charging = on_off
        if on_off == "off":
            zaptec.stop_charging(device_id=self.charger_id)
        else:
            zaptec.resume_charging(device_id=self.charger_id)


class Calculations:

    def __init__(self, house: House, charger: Charger, options: Options) -> None:
        # todo put charger.load_power in avaliable power calculations maybe do an if statement checking if charging is on
        self.house_only_load_power = max(0, house.load_power - charger.load_power)
        self.available_solar_power = max(
            0, house.solar_power - self.house_only_load_power
        )  # maybe put - 100
        self.bat_has_charge = house.battery_charge > options.battery_min
        self.solar_max_power = max(0, house.SOLAR_MAX - self.house_only_load_power)
        self.available_battery_power = max(
            0, house.INVERTER_MAX - self.house_only_load_power
        )

        self.slow_battery_power = max(
            self.available_battery_power, self.solar_max_power
        )
        self.fast_battery_power = min(
            self.available_solar_power + self.available_battery_power,
            house.INVERTER_MAX,
        )
        self.solar_power = min(self.available_solar_power, self.solar_max_power)
        self.grid_power = kw(7.36)

        self._set_states()

    def _set_states(self) -> None:
        for key, value in self.__dict__.items():
            attributes = {
                "device_class": "power",
                "unit": "W",
                "state_class": "measurement",
            }
            if key == "bat_has_charge":
                attributes = {"device_class": "boolean"}
            if not key.startswith("_"):
                state.set(
                    var_name=f"dylscript.{key}", value=value, new_attributes=attributes
                )


def set_6_amps(charger: Charger) -> None:
    charger.set_current_limit(6)
    charger.switch_charger("on")
    return None


def get_new_power(
    charge_type: str, calc: Calculations, charger: Charger
) -> float | None:
    power_map = {
        "Slow-Battery (Battery or Solar)": (
            calc.slow_battery_power if calc.bat_has_charge else calc.solar_power
        ),
        "Battery (Battery & Solar)": (
            calc.fast_battery_power if calc.bat_has_charge else calc.solar_power
        ),
        "Solar": calc.solar_power,
        "Grid": calc.grid_power,
        "6 Amps (Slowest)": set_6_amps(charger),
    }

    return power_map.get(charge_type, calc.solar_power)


@service
def sync_car_to_solar() -> None:
    options = Options()
    charger = Charger()

    if options.charge_type == "Off":
        charger.set_power_limit(0)
        return ""

    house = House()

    calc = Calculations(house, charger, options)

    new_power = None

    new_power = get_new_power(options.charge_type, calc, charger)

    if new_power:
        state.set(
            var_name=f"dylscript.new_power",
            value=new_power,
            new_attributes={
                "device_class": "power",
                "unit": "W",
                "state_class": "measurement",
            },
        )
        charger.set_power_limit(new_power)
