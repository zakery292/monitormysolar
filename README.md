#Monitor My Solar Home assistant integration
This solution was devloped to take over from where others have started, this integration only works with hardware purchased from us directly at https://monitormy.solar
This integration is designed to make adding your inverter to home assistant without the complexity of creating modbus solutions or other funky hardware the dongle is designed to plug in and replace your current dongle connected to your inverter
for some brands not others (listed below) you can use our dongle to communicate with the manufacturers portal as well as our own and home assistant. 
 - Lux Power

#What is this and what does it do? 
This integration is as simple as it sounds, connect the dongle get all the entites and sensors your inverter has to offer with read and write capabilities. 

#What inverters do you support? 
We support the following inverters in home assistant and our monitoring portal 
- Lux Power
- Solis (coming soon)
- Solax (coming Soon)
- Growwatt (coming soon)

## Want other inverters? submit a issue and we will look into the most popular ones

# Now the important part! How to install?
## Follow the steps below to get this installed and working
- Download the integration through hacs
- Ensure you have MQTT running within your home assistant enviroment or a seperate broker
- connect to your dongle either over your local network or via the dongles wifi
- select the option for local MQTT server
- put in the ip address of home assistant in this format ```mqtt://123.456.7.89:1883``` or the equivilent of what your ip address is
- if your mqtt broker requires a username and password then put this in the boxes hit save the dongle will reboot
- in homeassistant you do the same start the integration if your using the local home assistant broker you should be able to leave the field as is then select your inverter and then start

That should be it. Nothing to confgure nothing to change you should now be getting readings
Settings upadate every 5 minutes, sensors every second or so. 
