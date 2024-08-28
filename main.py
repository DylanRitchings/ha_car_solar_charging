from dataclasses import dataclass


def kw(value: str):
    return float(value)*1000


def watt(value: str):
    return float(value)


@dataclass
class House:
    def __init__(self):
        self.INVERTER_MAX = kw(2.67)
        self.SOLAR_MAX = kw(3.67)

        self.solar_power = kw(sensor.foxess_solar_power)
        self.load_power = kw(sensor.foxess_load_power)
        self.grid_consumption = watt(
            sensor.octopus_energy_electricity_23l3042499_2700008005722_current_demand)
        self.battery_charge = float(sensor.foxess_bat_soc)


@dataclass
class Options:

    def __init__(self):
        self.charge_type = input_select.car_charging
        self.battery_min = 30


@dataclass
class Charger:

    def __init__(self):
        self.CHARGE_VOLTS = 230
        self.house_id = "e658d337f118a91c07ecc90b1482f639"  # move to state
        self.charger_id = "78ca94b33412b017cf3b53429b9a0b49"  # move to state
        self.load_power = max(0, float(sensor.car_charging_kw))
        self.available_current = float(
            state.get("number.28_oriel_road_available_current"))

    def to_current(self, power):
        return watt(power)/self.CHARGE_VOLTS

    def set_power_limit(self, new_load_power):

        current = self.to_current(new_load_power)
        if current < 6:
            self.set_current_limit(0)
            self.switch_charger("off")
            return ""
        elif self.available_current != current:
            self.set_current_limit(current)
        self.switch_charger("on")

    def set_current_limit(self, current: float):
        log.warning(f"limit current: {int(current)}")
        zaptec.limit_current(
            blocking=False,
            return_response=False,
            device_id=self.house_id,
            available_current=int(current)
        )

    def switch_charger(self, on_off: str):
        switch.charger_charging = on_off
        if on_off == "off":
            zaptec.stop_charging(device_id=self.charger_id)
        else:
            zaptec.resume_charging(device_id=self.charger_id)


@service
def sync_car_to_solar():
    options = Options()
    charger = Charger()

    if options.charge_type == "Off":
        charger.switch_charger("off")
        return ""

    house = House()

    house_only_load_power = house.load_power - charger.load_power

    # TODO remove normalized to 0 bit
    house_only_load_power = max(0, house_only_load_power)
    # todo if house_only_load_power is negative increase power, if positive reduce power

    available_solar_power = max(
        0, house.solar_power - house_only_load_power)  # maybe put - 100

    bat_has_charge = house.battery_charge > options.battery_min

    solar_max_power = max(0, house.SOLAR_MAX - house_only_load_power)

    # TODO or is it available_solar_power
    available_battery_power = max(
        0, house.INVERTER_MAX - house_only_load_power)

    new_power = 0
    log.warning("charge_type: " + options.charge_type)
    if options.charge_type == "Slow-Battery (Battery or Solar)" and bat_has_charge:
        new_power = max(available_battery_power, available_solar_power)
    elif options.charge_type == "Battery (Battery & Solar)" and bat_has_charge:

        new_power = min(available_solar_power+available_battery_power,
                        house.INVERTER_MAX)  # TODO or solar_max_power
        log.warning(new_power)
    elif options.charge_type == "Solar" or ("Battery" in options.charge_type and not bat_has_charge):
        new_power = min(available_solar_power, solar_max_power)
    elif options.charge_type == "Grid":
        new_power = kw(7.36)
    elif options.charge_type == "6 Amps (Slowest)":
        charger.limit_current(6)
        charger.switch_charger("on")
        return ""

    charger.set_power_limit(new_power)
