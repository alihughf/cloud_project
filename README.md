# cloud_project
ECS781 coursework mini-project 
Name: Alastair Foster
Student ID: 190674973
This Api is used to find out information about assets in the game Age of Empires II.
Inside are instructions to set up a cassandra database to store a list of game assets from 4 different categories, civilisations, technologies, structures and units. The information is in the 4 csvs and has the id number for each asset.
The full.py program has functionality to:
1. Get these lists or to ask for the id of a single item on the list.
2. Add a new item to any of the list, providing its name or id isn't already there.
3. Change the name of an item of a certain id
4. Remove an item from the list by id number.

Functionality added from an external api in the full.py app is a get request to the https://age-of-empires-2-api.herokuapp.com/docs/#/ api to get more detailed statistics on any of the assets that are listed in the 4 tables. This can be done by specifying which of the 4 categories the asset belongs to and then giving either its name or id number.
