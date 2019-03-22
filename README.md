# Project 4 Catalog 
This is the 4th project for the Udacity Full Stack Nano-degree.
The goal of this project was to develop a flask catalog application
with a database backend that can perform CRUD operations. The wed app 
is protected using google Authorization. 
My Project is a wish list application. 

### Getting the Repository
The easiest way to get the project is by forking this repository and cloning it onto
you local machine. You will need git for this.

### Before Running this application 
You will need a VM in order to run this application. If you have access
to the Udacity Full Stack Nano-Degree, you may have already set up a Vagrant
 VM. Instructions for set up are below.
 
 
 You will need to download and install both 
 [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) and
 [Vagrant](https://www.vagrantup.com/downloads.html). 
 
 To make things easier, you can fork the 
 [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm)
 and clone it to your local machine.
 
 To bring up the VM, go to the `vagrant` directory inside the directory you 
 just cloned. Using the command `vagrant up` will start the machine. The First 
 time you initialize the machine will take a few minutes. Once the VM is up, 
 use the command `vagrant ssh` to connect to the VM. Running the included `pg_config.sh` 
  should install all required libraries. The `/vagrant` is your shared directory.
  
  
  To set up the database and populate it with a sample list and user, run the following commands
  ````
  pyhton /path/to/database_set.py
  python /path/to/wish_list_sample_data.py
  ````
  
 ### Running the Application
  From here you can run 
  ````
  python /path/to/project.py
````

This will start the flask application. To view the application point a internet browser to 
[http://localhost:5000](http://localhost:5000) . If you cannot see the app, check your Vagrantfile, it is possible 
the port is forwarded to another port.

### Using the Wish List Application

 Aside from using the UI, JSON endpoints are set up to expose the information in the app, as JSON objects. These endpoints are
 
 [http://localhost:5000/wish_list/1/item/1/JSON](http://localhost:5001/wish_list/1/item/1/JSON)
 
 [http://localhost:5000/wish_list/1/list/JSON](http://localhost:5001/wish_list/1/list/JSON)
 
 [http://localhost:5001/wish_list/JSON](http://localhost:5001/wish_list/JSON)
 
 #### Technologies Used
 * python
 * flask
 * bootstrap
 * sqlalchemy
 * google authorization
 * Oauth 
 
 ##### References
 * This application is modeled after the Restaurant App exercise that is part of the  Udacity Full Stack NanoDegree. 
 * Due to google retiring google+, google authentication was done following the login.html found [here](https://gist.github.com/shyamgupta/d8ba035403e8165510585b805cf64ee6)
 
 
 
 
  