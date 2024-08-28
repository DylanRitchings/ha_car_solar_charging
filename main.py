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
        self.charge_type = input_select.car_charging
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
        
                                     
    def set_current_limit(self, new_load_power):          
        current = to_current(new_load_power)
        
        if self.available_current != charge_amps:
            self._limit_current(current)
            zaptec.resume_charging(device_id=self.charger_id)
            self.switch_charger("on")

    def _limit_current(self, current: float):
        zaptec.limit_current(blocking=False, return_response=False, device_id=self.house_id, available_current=current)
    
    def switch_charger(self, on_off: str):
        switch.charger_charging = on_off

    def 
    
def main():
    house = House()
    options = Options()
    charger = Charger()

@service
def sync_car_to_solar():
    """sync car to solar"""

    

    try:
        log.warning(charge_type)
        log.warning(automation.car_charging)
        if charge_type == "Off":
            log.warning("Turn charging off")
            zaptec.stop_charging(device_id="78ca94b33412b017cf3b53429b9a0b49")
            log.warning(automation.car_charging)
            switch.charger_charging = "off"
            return ""

            
        solar_power = float(sensor.foxess_solar_power)
        #log.warning(f"solar power: {solar_power}")
        

        current_charge_power = max(0, float(sensor.car_charging_kw))
        #log.warning(f"current charge power: {current_charge_power}")
        before_load_power = float(sensor.foxess_load_power) - current_charge_power
        load_power = max(0, before_load_power)
        
        #log.warning(f"before load power: {before_load_power}")
        
        #log.warning(f"foxess_load_power: {sensor.foxess_load_power}")

        #TODO fix charging going to 0 due to load_power being taken away from solar_oower
        available_solar = max(0, solar_power - load_power - 0.1)
        #available_solar = max(0, solar_power - 0.1)

        log.warning(f"available_solar: {available_solar}")
        
        grid_consumption = float(sensor.foxess_grid_consumption_power)
        
        #log.warning(f"grid_consumption: {grid_consumption}")
        
        bat_has_charge = float(sensor.foxess_bat_soc) > float(25)
        
            
        max_power = max(0, SOLAR_MAX_KW - load_power - 0.1)
        #max_power = max(0, SOLAR_MAX_KW)
        #log.warning(f"max_power: {max_power}")
        
        available_bat_load = max(0, INVERTER_MAX_KW - load_power)
        
        if charge_type=="Slow-Battery (Battery or Solar)" and bat_has_charge:
        
            charge_kw = max(available_bat_load, available_solar)
            
        elif charge_type=="Battery (Battery & Solar)" and bat_has_charge:
            
            log.warning("BATTERY")
            
            
            charge_kw = min(available_solar+available_bat_load, max_power)
            #charge_kw = max(available_bat_load, available_solar)# - grid_consumption
            #TODO add rest of solar to 2.7 to get actual value
               
        elif charge_type=="Solar" or ("Battery" in charge_type and not bat_has_charge):
            charge_kw = min(available_solar, max_power)# - grid_consumption
        elif charge_type=="Grid":
            charge_kw = 7.36
        elif charge_type=="6 Amps (Slowest)":
            zaptec.limit_current(blocking=False, return_response=False, device_id="e658d337f118a91c07ecc90b1482f639", available_current=6)
            return ""
            
        log.warning(f"charge_kw: {charge_kw}")
        
        charge_amps = (charge_kw*1000)/CHARGE_VOLTS
        
        charge_amps_floored = int(charge_amps)
        
        if charge_amps_floored < 6:
            zaptec.stop_charging(device_id="78ca94b33412b017cf3b53429b9a0b49")
            switch.charger_charging = "off"

        elif int(float(state.get("number.28_oriel_road_available_current"))) != charge_amps_floored:
            #log.warning(f"charge amps: {charge_amps_floored}")
            log.warning(f"limit current to: {charge_amps_floored} A")
            zaptec.limit_current(blocking=False, return_response=False, device_id="e658d337f118a91c07ecc90b1482f639", available_current=charge_amps_floored)
            zaptec.resume_charging(device_id="78ca94b33412b017cf3b53429b9a0b49")
            switch.charger_charging = "on"
        else:
            log.warning("Turn charging on")
            zaptec.resume_charging(device_id="78ca94b33412b017cf3b53429b9a0b49")
            switch.charger_charging = "on"
        

        
        #state.set("number.28_oriel_road_available_current", value=charge_amps_floored)
    except Exception as e:
        log.error(e)
        #service.call(domain="zaptec", name="limit_current", available_current=0.0, device_id="e658d337f118a91c07ecc90b1482f639")
        #zaptec.limit_current(blocking=False, return_response=False, device_id="e658d337f118a91c07ecc90b1482f639", available_current=0.0)
