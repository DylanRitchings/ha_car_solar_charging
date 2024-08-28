from dataclasses import dataclass

def kw(value: str):
    return float(value)*1000

def watt(value: str):
    return float(value)
    
@dataclass
class House:
    INVERTER_MAX = kw(2.67)
    SOLAR_MAX = kw(3.67)
    
    solar_power: float 
    load_power: float 
    grid_consumption: float 
    battery_charge: float

    #TODO maybe put options and charger in here?
    
    def __init__(self):
        self.solar_power = kw(sensor.foxess_solar_power)
        self.load_power = kw(sensor.foxess_load_power)
        self.grid_consumption = watt(sensor.octopus_energy_electricity_23l3042499_2700008005722_current_demand)
        self.battery_charge = float(sensor.foxess_bat_soc)
        

@dataclass
class Options:
    battery_min: int # %
    charge_type: str
    
    def __init__(self):
        self.charge_type = lower(input_select.car_charging)
        self.battery_min = 30
        

@dataclass
class Charger:
    CHARGE_VOLTS = 230
    
    load_power: float
    available_current: float

    house_id: str = "e658d337f118a91c07ecc90b1482f639" # move to state
    charger_id: str = "78ca94b33412b017cf3b53429b9a0b49" # move to state
    
    def __init__(self):
        self.load_power = max(0, float(sensor.car_charging_kw))
        self.available_current = int(float(state.get("number.28_oriel_road_available_current"))

    def to_current(power):
        return watt(power)/self.CHARGE_VOLTS
        
                                     
    def set_power_limit(self, new_load_power):          
        current = to_current(new_load_power)
        if charge_amps_floored < 6:
            self.switch_charger("off")
            return ""
        elif self.available_current != charge_amps:
            self.set_current_limit(current)        
        self.switch_charger("on")

    def set_current_limit(self, current: float):
        zaptec.limit_current(blocking=False, return_response=False, device_id=self.house_id, available_current=current)
    
    def switch_charger(self, on_off: str):
        switch.charger_charging = on_off
        if on_off = "off":
            zaptec.stop_charging(device_id=self.charger_id)
        else:
            zaptec.resume_charging(device_id=self.charger_id)


@service 
def main():
    options = Options()
    charger = Charger()

    if options.charge_type == "off":
        charger.switch_charger("off")
        return ""

    house = House()

    house_only_load_power = house.load_power - charger.load_power 
    
    house_only_load_power = max(0, house_only_load_power) # TODO remove normalized to 0 bit
    # todo if house_only_load_power is negative increase power, if positive reduce power
    
    available_solar_power = max(0, house.solar_power - house_only_load_power) # maybe put - 100

    bat_has_charge = house.battery_charge > options.battery_min

    solar_max_power = max(0, house.SOLAR_MAX - house_only_load_power)

    available_battery_power = max(0, house.INVERTER_MAX - house_only_load_power) # TODO or is it available_solar_power
    
    new_power = 0
    
    if options.charge_type=="Slow-Battery (Battery or Solar)" and bat_has_charge:
        new_power = max(available_bat_load, available_solar_power) 
    elif options.charge_type=="Battery (Battery & Solar)" and bat_has_charge:
        new_power = min(available_solar_power+available_battery_power, solar.INVERTER_MAX) # TODO or solar_max_power
    elif options.charge_type=="Solar" or ("Battery" in options.charge_type and not bat_has_charge):
        new_power = min(available_solar, solar_max_power)
    elif options.charge_type=="Grid":
        new_power = kw(7.36)
    elif charge_type=="6 Amps (Slowest)":
        charger.limit_current(6)
        charger.switch_charger("on")
        return ""


    charger.set_power_limit(new_power)
