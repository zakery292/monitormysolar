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
## Step 1:
 - For the installation of this integration you will need to have a working home assistant installation, if you do not have one you can get one here https://www.home-assistant.io/installation/
 - Once you have a working Home Assistant Instatllation you will need to install the Mosquitto broker, this is the broker that will be used to communicate with the dongle and home assistant. I will assume you have done this and know what your doing here, these instructions will not  go into detail on how to install the Mosquitto broker nor will we assist you with the installation of the broker.
 - I will also assume you have HACS installed and know how to use it, if you do not have HACS installed you can get it here https://hacs.xyz/docs/setup/prerequisites Again if you do not know how to use HACS please do not use this integration.
 ### Step 1.1:
 - Head to HACS and (depending on when your reading this you might have to add as a custom repository) click the three dots in the top right corner and select "Custom repositories"
 [![image](images/step1.png)]
 - Copy the URL of this page and  paste it into the "Repository URL" field and click "Add"
 [![image](images/step1.1.png)]
 - Once added depending on how quick you are it'll either be right there at the top of list or you will need to seach for it. Once found on the end of the row click the three dots and select "Download"
 [![image](images/step1.3.png)]
 [![image](images/step1.4.png)]
 - Once downloaded you will need to restart home assistant for the integration to be loaded
 [![image](images/step1.5.png)]
 ## Step 2:
 - Once Home Assistant has restarted you will need to go to Settings -> Devices & Services -> Add Integration
 [![image](images/step2.png)]
 [![image](images/step2.1.png)]
 - In the popup that appears search for "Monitor My Solar" and click on the integration
 [![image](images/step2.2.png)]
 - Before going any further you will need the "dongle-ID" You can find this on the webpage that the dongle provides when you connect directly to it. If you know the IP address of your dongle you should be able to put that in your browser to get to the dongle config page. Once on the dongle config page we need to set up the home assistant MQTT Server settings. 
 [![image](images/step2.3.png)]
 - On the Dongle config page Click the box "Enable Local MQTT Server", fill out the MQTT Server Address this will be ```mqtt://<IP ADDRESS OF HOME ASSISTANT>:1883```, fill out the MQTT Server Username and MQTT Server Password with the credentials you set up in Home Assistant for Mosquitto (you can use your username and password although this is not recomended). Once done click save. The dongle will restart. IF YOU DO NOT FOLLOW THIS STEP IT WILL NOT WORK AND YOU WILL NOT BE GIVEN ANY HELP. DONGLE SETUP FIRST BEOFRE INTEGRATION SETUP.
 [![image](images/step2.4.png)]
 - Dongle ID is presented at the bottom of the configpage for home assistant you will need to change the capitalization of Dongle to lowercase dongle.
 - Once you have the Dongle-ID and you have set up the MQTT server on the dongle (youll see connected on the webpage if its worked under local MQTT server) you can go back to home assistant and finish the integration setup.
 - For the integration Select the inverter your setting up, if your using the Mosquitto broker then leave the server as default, port as default and enter the username and password you set up in Home Assistant for Mosquitto. Enter the dongle-ID from the dongle config page. press submit.
 [![image](images/step2.5.png)]
 ## Step 3: 
 - If you followed these instruction and did not deviate then you will be presented with a popup like the below image. 
 [![image](images/step3.png)]
 - If you are presented with this popup then you are complete. 
 - If you are not presented with this popup then you have done something wrong and you will need to go back and check your work. If you are still stuck please open a issue on the github page and we will try to help you.

 # FAQ
 - Q: Can i use a External MQTT Broker? 
 - A: Yes you can, for the Dongle just put the IP Address of the MQTT broker in the server address filed and enter the username and password, in Home assistant you need to change core-mosquitto to the IP of the MQTT broker.
 - Q: It didnt work?
 - A: There is not much i can do for you. You need to check your work and make sure you have done everything correctly. If you are still stuck please open a issue on the github page and we will try to help you.
 - Q: It created the integration, told me to check the logs and it said firmware response timeout.
 - A: This is a issue with the donlge or home assistant not being connected to the broker. I suggest to help you debug the issue you download MQTTFX, connect to the broker and subscribe to the topic dongle-id/#, reboot the dongle, reboot homeassitant, delete the integration, reinstall and try again you should see a topic called dongle-id/firmware-request and then another with /firmware-response, if you see both of these raise a issue include pictures of the logs or the logs in general. 
 - Q: I have a question that is not answered here.
 - A: Please open a issue on the github page and we will try to help you.


