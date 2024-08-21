"""Constants for Inverter MQTT."""
from logging import Logger, getLogger
from homeassistant.const import (
    CONF_MODE,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

Logger: Logger = getLogger(__package__)

# Domain for the integration
DOMAIN = "inverter_mqtt"


FIRMWARE_CODES = {
    "a_3_6k_Hybrid": {
        "Device_Type": "A Standard model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "High Voltage Battery Version",
            "C": "Gen 3-6k"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "US Model"
        }
    },
    "B_AC_Coupled": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "E_8_10K_Hybrid": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "F_12K_Hybrid": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    },
    "G_3Phase_Hybrid": {
        "Device_Type": "A Standard Model",
        "Derived_Device_Type": {
            "A": "Standard Model",
            "B": "Others",
            "C": "Others"
        },
        "ODM_Code": {
            "A": "Luxpower",
            "B": "Others",
            "C": "Others"
        },
        "Feature_Code": {
            "A": "Standard Model",
            "B": "Parallel Model",
            "C": "Others"
        }
    }
}

# Default MQTT configuration for Home Assistant broker
DEFAULT_MQTT_SERVER = "mqtt://core-mosquitto"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_USERNAME = ""
DEFAULT_MQTT_PASSWORD = ""



ENTITIES = {
        "Lux": {
            "sensors": {
                "inputbank1": [
                    {"name": "State", "type": "sensor", "unique_id": "state"},
                    {"name": "Voltage PV1", "type": "sensor", "unique_id": "vpv1", "unit_of_measurement": "V", "device_class": "voltage"},
                    {"name": "Voltage PV2", "type": "sensor", "unique_id": "vpv2", "unit_of_measurement": "V", "state_class": "measurement", "device_class": "voltage"},
                    {"name": "Voltage PV3", "type": "sensor", "unique_id": "vpv3", "unit_of_measurement": "V", "state_class": "measurement", "device_class": "voltage", "allowed_device_types": ["E", "F", "G"]},
                    {"name": "Voltage Battery", "type": "sensor", "unique_id": "vbat", "unit_of_measurement": "V", "state_class": "measurement", "device_class": "voltage"},
                    {"name": "State of Charge", "type": "sensor", "unique_id": "soc", "state_class": "measurement", "unit": "%"},
                    {"name": "State of Health", "type": "sensor", "unique_id": "soh", "state_class": "measurement", "unit": "%"},
                    {"name": "Internal Fault", "type": "sensor", "unique_id": "internal_fault", "state_class": "measurement"},
                    {"name": "Power PV1", "type": "sensor", "unique_id": "ppv1", "state_class": "measurement", "unit": "W"},
                    {"name": "Power PV2", "type": "sensor", "unique_id": "ppv2", "state_class": "measurement", "unit": "W"},
                    {"name": "Power PV3", "type": "sensor", "unique_id": "ppv3", "state_class": "measurement", "unit": "W", "allowed_device_types": ["E", "F", "G"]},
                    {"name": "Power Charge", "type": "sensor", "unique_id": "pcharge", "state_class": "measurement", "unit": "W"},
                    {"name": "Power Discharge", "type": "sensor", "unique_id": "pdischarge", "state_class": "measurement", "unit": "W"},
                    {"name": "Voltage AC R", "type": "sensor", "unique_id": "vacr", "state_class": "measurement", "unit": "V"},
                    {"name": "Voltage AC S", "type": "sensor", "unique_id": "vacs", "state_class": "measurement", "unit": "V", "allowed_device_types": ["G"]},
                    {"name": "Voltage AC T", "type": "sensor", "unique_id": "vact", "state_class": "measurement", "unit": "V", "allowed_device_types": ["G"]},
                    {"name": "Frequency AC", "type": "sensor", "unique_id": "fac", "state_class": "measurement", "unit": "Hz"},
                    {"name": "Power Inverter", "type": "sensor", "unique_id": "pinv", "state_class": "measurement", "unit": "W"},
                    {"name": "Power Rectifier", "type": "sensor", "unique_id": "prec", "state_class": "measurement", "unit": "W"},
                    {"name": "Current Inverter RMS", "type": "sensor", "unique_id": "iinvrms", "state_class": "measurement", "unit": "A"},
                    {"name": "Power Factor", "type": "sensor", "unique_id": "pf", "state_class": "measurement"},
                    {"name": "Voltage EPS R", "type": "sensor", "unique_id": "vepsr", "state_class": "measurement", "unit": "V"},
                    {"name": "Voltage EPS S", "type": "sensor", "unique_id": "vepss", "state_class": "measurement", "unit": "V", "allowed_device_types": ["G"]},
                    {"name": "Voltage EPS T", "type": "sensor", "unique_id": "vepst", "state_class": "measurement", "unit": "V", "allowed_device_types": ["G"]},
                    {"name": "Frequency EPS", "type": "sensor", "unique_id": "feps", "state_class": "measurement", "unit": "Hz"},
                    {"name": "Power EPS", "type": "sensor", "unique_id": "peps", "state_class": "measurement", "unit": "W"},
                    {"name": "Apparent Power EPS", "type": "sensor", "unique_id": "seps", "state_class": "measurement", "unit": "VA"},
                    {"name": "Power to Grid", "type": "sensor", "unique_id": "ptogrid", "state_class": "measurement", "unit": "W"},
                    {"name": "Power to User", "type": "sensor", "unique_id": "ptouser", "state_class": "measurement", "unit": "W"},
                    {"name": "Energy PV1 Day", "type": "sensor", "unique_id": "epv1_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy PV2 Day", "type": "sensor", "unique_id": "epv2_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy PV3 Day", "type": "sensor", "unique_id": "epv3_day", "state_class": "measurement", "unit": "kWh", "allowed_device_types": ["E", "F", "G"]},
                    {"name": "Energy Inverter Day", "type": "sensor", "unique_id": "einv_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Rectifier Day", "type": "sensor", "unique_id": "erec_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Charge Day", "type": "sensor", "unique_id": "echg_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Discharge Day", "type": "sensor", "unique_id": "edischg_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy EPS Day", "type": "sensor", "unique_id": "eeps_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy to Grid Day", "type": "sensor", "unique_id": "etogrid_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy to User Day", "type": "sensor", "unique_id": "etouser_day", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Voltage Bus 1", "type": "sensor", "unique_id": "vbus1", "state_class": "measurement", "unit": "V"},
                    {"name": "Voltage Bus 2", "type": "sensor", "unique_id": "vbus2", "state_class": "measurement", "unit": "V"},
                ],
                "inputbank2": [
                    {"name": "Energy PV1 All", "type": "sensor", "unique_id": "epv1_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy PV2 All", "type": "sensor", "unique_id": "epv2_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy PV3 All", "type": "sensor", "unique_id": "epv3_all", "state_class": "measurement", "unit": "kWh", "allowed_device_types": ["E", "F", "G"]},
                    {"name": "Energy Inverter All", "type": "sensor", "unique_id": "einv_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Rectifier All", "type": "sensor", "unique_id": "erec_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Charge All", "type": "sensor", "unique_id": "echg_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy Discharge All", "type": "sensor", "unique_id": "edischg_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy EPS All", "type": "sensor", "unique_id": "eeps_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy to Grid All", "type": "sensor", "unique_id": "etogrid_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Energy to User All", "type": "sensor", "unique_id": "etouser_all", "state_class": "measurement", "unit": "kWh"},
                    {"name": "Fault Code", "type": "sensor", "unique_id": "fault_code", "state_class": "measurement"},
                    {"name": "Warning Code", "type": "sensor", "unique_id": "warning_code", "state_class": "measurement"},
                    {"name": "Internal Temperature", "type": "sensor", "unique_id": "tinner", "state_class": "measurement", "unit": "°C"},
                    {"name": "Radiator Temperature 1", "type": "sensor", "unique_id": "tradiator1", "state_class": "measurement", "unit": "°C"},
                    {"name": "Radiator Temperature 2", "type": "sensor", "unique_id": "tradiator2", "state_class": "measurement", "unit": "°C", "allowed_device_types": ["E", "F", "G"]},
                    {"name": "Battery Temperature", "type": "sensor", "unique_id": "tbat", "state_class": "measurement", "unit": "°C"},
                    {"name": "Running Time", "type": "sensor", "unique_id": "running_time", "state_class": "measurement", "unit": "s"},
                    {"name": "Auto Test Limit", "type": "sensor", "unique_id": "wAutoTestLimit", "state_class": "measurement"},
                    {"name": "Auto Test Default Time", "type": "sensor", "unique_id": "uwAutoTestDefaultTime", "state_class": "measurement"},
                    {"name": "Auto Test Trip Value", "type": "sensor", "unique_id": "uwAutoTestTripValue", "state_class": "measurement"},
                    {"name": "Auto Test Trip Time", "type": "sensor", "unique_id": "uwAutoTestTripTime", "state_class": "measurement"},
                    {"name": "AC Input Type", "type": "sensor", "unique_id": "ACInputType", "state_class": "measurement"},
                ],
                "holdbank1" : [
                    {"name": "FWCode", "type": "sensor", "unique_id": "FWCode", "state_class": "text"},
                    {"name": "Slave Version", "type": "sensor", "unique_id": "SlaveVer", "state_class": "text"},
                    {"name": "Com Version", "type": "sensor", "unique_id": "ComVer", "state_class": "text"},
                    {"name": "Control Version", "type": "sensor", "unique_id": "CntlVer", "state_class": "text"},
                    {"name": "FW Version", "type": "sensor", "unique_id": "FWVer", "state_class": "text"},
                    {"name": "Date Time", "type": "sensor", "unique_id": "time_Date_combined", "state_class": "text"},

                ]
            },
            "switch": {
                "holdbank1": [
                    {"name": "Restart Inverter", "type": "switch", "unique_id": "ResetSetting"},
                    {"name": "EPS", "type": "switch", "unique_id": "EPS"},
                    {"name": "Ground neutral detectionenable", "type": "switch", "unique_id": "NeutralDetect"},
                    {"name": "AC Charge", "type": "switch", "unique_id": "ACCharge"},
                    {"name": "seamless off-grid mode switching ", "type": "switch", "unique_id": "SWSeamlessly"},
                    {"name":"Standby Switch", "type": "switch", "unique_id": "SetToStandby"},
                    {"name":"Force Discharge", "type": "switch", "unique_id": "ForcedDischg"},
                    {"name":"Charge Priority", "type": "switch", "unique_id": "ForcedChg"},
                    {"name":"Export Allowed", "type": "switch", "unique_id": "FeedInGrid"},
                ],
                "holdbank3": [
                    {"name": "PV Grid Off", "type": "switch", "unique_id": "ubPVGridOffEn" }, #"allowed_device_types": ["A", "B", "E", "F", "G"]},
                    {"name": "Fast Zero Export", "type": "switch", "unique_id": "ubFastZeroExport"}, #"allowed_device_types": ["A", "B", "E", "F", "G"]},
                    {"name": "Micro Grid On", "type": "switch", "unique_id": "ubMicroGridEn"}, #"allowed_device_types": ["A", "B", "E", "F", "G"]},
                    {"name": "Battery Shared", "type": "switch", "unique_id": "ubBatShared"}, #"allowed_device_types": ["A", "B", "E", "F", "G"]},
                    {"name": "Charge Last", "type": "switch", "unique_id": "ubChgLastEn"}, #"allowed_device_types": ["A", "B", "E", "F", "G"]},
                ],
                "holdbank4": [
                    {"name": "Half hour charge Switch", "type": "switch", "unique_id": "HalfHourACChrStartEn"},
                ],

            },
            "number": {
                "holdbank2": [
                    {"name": "Active Power", "type": "number", "unique_id": "ActivePowerPercentCMD", "unit": "PERCENT", "min": 0, "max": 100 , "mode": "slider"},
                    {"name": "Charge Power Rate", "type": "number", "unique_id": "ChargePowerPercentCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},
                    {"name": "Discharge Power Rate", "type": "number", "unique_id": "DischargePowerPercentCMD", "unit": "PERCENT", "min": 0, "max": 100 , "mode": "slider"},
                    {"name": "AC Charge Rate", "type": "number", "unique_id": "ACChgPowerCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},
                    {"name": "SOC Limit", "type": "number", "unique_id": "ACChgSOCLimit", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider", "class": "BATTERY"},
                    {"name": "Charge First Rate", "type": "number", "unique_id": "ChgFirstPowerCMD", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},
                    {"name": "Charge First SOC Limit", "type": "number", "unique_id": "ChgFirstSOCLimit", "unit": "PERCENT", "min": 0, "max": 100, "mode": "slider"},
                ],
                "holdbank3": [
                    {"name": "Force Discharge Power Rate", "type": "number", "unique_id": "ForcedDischgPowerCMD", "unit": "PERCENT", "min": 0, "max": 100 , "mode": "slider"},
                    {"name": "Force Discharge SOC Limit", "type": "number", "unique_id": "ForcedDischgSOCLimit", "unit": "PERCENT", "min": 0, "max": 100 , "mode": "slider"},
                    {"name": "Lead acid Charge Rate (A)", "type": "number", "unique_id": "ChargeRate", "unit": "A", "min": 0, "max": 140 , "mode": "slider", "native_unit": "A", "class": "CURRENT"},
                    {"name": "Lead Acid Discharge Rate (A)", "type": "number", "unique_id": "DischgRate", "unit": "A", "min": 0, "max": 140 , "mode": "slider", "native_unit": "A", "class": "CURRENT"},
                    {"name": "Battery Discharge Start Point (W)", "type": "number", "unique_id": "PtoUserStartdischg", "unit": "W", "min": 1, "max": 50 , "mode": "slider", "native_unit": "W", "class": "POWER"},
                    {"name": "Battery Charge Start Point (W)", "type": "number", "unique_id": "PtoUserStartchg", "unit": "W", "min": 1, "max": -50 , "mode": "slider", "native_unit": "W", "class": "POWER"},
                    {"name": "CT Offset (W)", "type": "number", "unique_id": "wCT_PowerOffset", "unit": "W", "min": 0, "max": 1000 , "mode": "slider", "native_unit": "W", "class": "POWER"},
                ],

            },
            "select": {
                "holdbank3": [
                    {"name": "CT Sample Ratio", "type": "select", "unique_id": "CTSampleRatio", "options": ["1:1000", "1:3000"]},
                    {"name": "Clear Parallel Alarm", "type": "select", "unique_id": "ClearParallelAlarm", "options": ["N/A", "Clear" ]},

                    # Add more selects as needed
                ],
                "holdbank4": [
                    {"name": "00:00 -- 00:30", "type": "select", "unique_id": "Time0", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "00:30 -- 01:00", "type": "select", "unique_id": "Time1", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "01:00 -- 01:30", "type": "select", "unique_id": "Time2", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "01:30 -- 02:00", "type": "select", "unique_id": "Time3", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "02:00 -- 02:30", "type": "select", "unique_id": "Time4", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "02:30 -- 03:00", "type": "select", "unique_id": "Time5", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "03:00 -- 03:30", "type": "select", "unique_id": "Time6", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "03:30 -- 04:00", "type": "select", "unique_id": "Time7", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "04:00 -- 04:30", "type": "select", "unique_id": "Time8", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "04:30 -- 05:00", "type": "select", "unique_id": "Time9", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "05:00 -- 05:30", "type": "select", "unique_id": "Time10", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "05:30 -- 06:00", "type": "select", "unique_id": "Time11", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "06:00 -- 06:30", "type": "select", "unique_id": "Time12", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "06:30 -- 07:00", "type": "select", "unique_id": "Time13", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "07:00 -- 07:30", "type": "select", "unique_id": "Time14", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "07:30 -- 08:00", "type": "select", "unique_id": "Time15", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "08:00 -- 08:30", "type": "select", "unique_id": "Time16", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "08:30 -- 09:00", "type": "select", "unique_id": "Time17", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "09:00 -- 09:30", "type": "select", "unique_id": "Time18", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "09:30 -- 10:00", "type": "select", "unique_id": "Time19", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "10:00 -- 10:30", "type": "select", "unique_id": "Time20", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "10:30 -- 11:00", "type": "select", "unique_id": "Time21", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "11:00 -- 11:30", "type": "select", "unique_id": "Time22", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "11:30 -- 12:00", "type": "select", "unique_id": "Time23", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "12:00 -- 12:30", "type": "select", "unique_id": "Time24", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "12:30 -- 13:00", "type": "select", "unique_id": "Time25", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "13:00 -- 13:30", "type": "select", "unique_id": "Time26", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "13:30 -- 14:00", "type": "select", "unique_id": "Time27", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "14:00 -- 14:30", "type": "select", "unique_id": "Time28", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "14:30 -- 15:00", "type": "select", "unique_id": "Time29", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "15:00 -- 15:30", "type": "select", "unique_id": "Time30", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "15:30 -- 16:00", "type": "select", "unique_id": "Time31", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "16:00 -- 16:30", "type": "select", "unique_id": "Time32", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "16:30 -- 17:00", "type": "select", "unique_id": "Time33", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "17:00 -- 17:30", "type": "select", "unique_id": "Time34", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "17:30 -- 18:00", "type": "select", "unique_id": "Time35", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "18:00 -- 18:30", "type": "select", "unique_id": "Time36", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "18:30 -- 19:00", "type": "select", "unique_id": "Time37", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "19:00 -- 19:30", "type": "select", "unique_id": "Time38", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "19:30 -- 20:00", "type": "select", "unique_id": "Time39", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "20:00 -- 20:30", "type": "select", "unique_id": "Time40", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "20:30 -- 21:00", "type": "select", "unique_id": "Time41", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "21:00 -- 21:30", "type": "select", "unique_id": "Time42", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "21:30 -- 22:00", "type": "select", "unique_id": "Time43", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "22:00 -- 22:30", "type": "select", "unique_id": "Time44", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "22:30 -- 23:00", "type": "select", "unique_id": "Time45", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "23:00 -- 23:30", "type": "select", "unique_id": "Time46", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},
                    {"name": "23:30 -- 24:00", "type": "select", "unique_id": "Time47", "options": ["Does Not Operate", "AC Charge", "PV Charge", "Discharge"]},


                    # Add more selects as needed
                ],
            },

            "time": {
                "holdbank1": [
                    {"name": "Date Combined", "type": "datetime", "unique_id": "time_date_combined", "native_value": "datetime", "icon": "mdi:calendar-clock"},

                ],
                "holdbank2": [
                    {"name": "AC Charge Start", "type": "time", "unique_id": "ACChgStart"},
                    {"name": "AC Charge End", "type": "time", "unique_id": "ACChgEnd"},
                    {"name": "AC Charge Start1", "type": "time", "unique_id": "ACChgStart1"},
                    {"name": "AC Charge End1", "type": "time", "unique_id": "ACChgEnd1"},
                    {"name": "AC Charge Start2", "type": "time", "unique_id": "ACChgStart2"},
                    {"name": "AC Charge End2", "type": "time", "unique_id": "ACChgEnd2"},
                    {"name": "Charge Priority Start", "type": "time", "unique_id": "ChgFirstEnd"},
                    {"name": "Charge Priority End", "type": "time", "unique_id": "ChgFirstStart"},
                    {"name": "Charge Priority Start1", "type": "time", "unique_id": "ChgFirstStart1"},
                    {"name": "Charge Priority End1", "type": "time", "unique_id": "ChgFirstEnd1"},
                ],
                "holdbank3": [
                    {"name": "Charge Priority Start2", "type": "time", "unique_id": "ChgFirstStart2"},
                    {"name": "Charge Priority End2", "type": "time", "unique_id": "ChgFirstEnd2"},
                    {"name": "ForcedDischgStart", "type": "time", "unique_id": "ForcedDischgStart"},
                    {"name": "ForcedDischgEnd", "type": "time", "unique_id": "ForcedDischgEnd"},
                    {"name": "ForcedDischgStart1", "type": "time", "unique_id": "ForcedDischgStart1"},
                    {"name": "ForcedDischgEnd1", "type": "time", "unique_id": "ForcedDischgEnd1"},
                    {"name": "ForcedDischgStart2", "type": "time", "unique_id": "ForcedDischgStart2"},
                    {"name": "ForcedDischgEnd2", "type": "time", "unique_id": "ForcedDischgEnd2"},
                ],
            },
        },

        "Solis": {
            "sensors": [
                {"name": "Energy", "type": "sensor", "unique_id": "energy", "state_class": "measurement", "unit": "kWh"},
                {"name": "Temperature", "type": "sensor", "unique_id": "temperature", "state_class": "measurement", "unit": "°C"},
            ],
            "numbers": [
                {"name": "Setpoint", "type": "number", "unique_id": "setpoint", "unit": "°C"},
            ],
        },
        "Solax": {
            "sensors": [
                {"name": "Battery Level", "type": "sensor", "unique_id": "battery_level", "state_class": "measurement", "unit": "%"},
            ],
            "switches": [
                {"name": "Inverter Status", "type": "switch", "unique_id": "inverter_status"},
            ],
        },
        "Growatt": {
            "sensors": [
                {"name": "Output Power", "type": "sensor", "unique_id": "output_power", "state_class": "measurement", "unit": "W"},
            ],
            "times": [
                {"name": "AC Charge Start1", "type": "time", "unique_id": "ac_charge_start1"},
                {"name": "AC Charge End1", "type": "time", "unique_id": "ac_charge_end1"},
            ],
        },
    }
