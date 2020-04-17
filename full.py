from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
import requests
import requests_cache

requests_cache.install_cache('aoe_api_cache', backend='sqlite', expire_after=36000)
cluster = Cluster(contact_points=['192.168.99.100'],port=9042)
session = cluster.connect()
app = Flask(__name__)

civ_url_template='https://age-of-empires-2-api.herokuapp.com/api/v1/civilization/{civ_id}'
struc_url_template='https://age-of-empires-2-api.herokuapp.com/api/v1/structure/{struc_id}'
tech_url_template='https://age-of-empires-2-api.herokuapp.com/api/v1/technology/{tech_id}'
unit_url_template='https://age-of-empires-2-api.herokuapp.com/api/v1/unit/{unit_id}'


@app.route('/')
def hello():
    name = request.args.get("name","User")
    return('<h1>Hello, {}!</h1>'.format(name))



@app.route('/list/<categ>', methods=['GET'])
def categs_list(categ):
    """A function that returns a list of id,name for all assets of a specified category (civiliations, structures, technologies, units)
    in the game Age of Empires 2 when the user navigates to the url /list/<categ>. The data is pulled from a cassandra db.
    Inputs:categ -- a category of assets in the Age of Empires 2 game that the user wishes to see the list of.
    Outputs:table -- a HTML table of id,name for all assets of the specified category."""

    data=session.execute("""Select id,name From aoe.{}""".format(categ)) #makes cql query of cassandra db
    table = "<TABLE border='1'>" #initialises html table
    
    for row in data:
       table+="<TR><TD>" + str(row.id) +"</TD><TD>"+row.name+"</TD><TR>" #adds a row to the table
    
    table+="</TABLE>" #closes off the html table
    
    return table, 200 #returns the table and a 200 ok response

@app.route('/list/<categ>',methods=['POST'])
def create_record(categ):
    """A function that is used to create a new record on one of the lists for any list category using a POST curl command
    Inputs: categ -- the target category table, specified in the url given in the curl command
    Outputs: multiple outputs depending on the curl command:
        if the request in the curl command isn't in json or the request does not have a name -- returns a 400 bad request response         
        if the command contained a name or id that already exists in the database -- returns 400 bad request response
        otherwise -- returns a 201 created response and details of the item created."""
    
    
    if not request.json or not 'name' in request.json:
        return jsonify({'error':'the new record must have a name and Id'}),400
    #searches for the target id
    id_test=session.execute("""Select count(*) from aoe.{} where id={}""".format((categ),request.json['id']))
    #checks if the target id is in the database
    for row in id_test:
        count_id=row.count
    #searches for the target name    
    name_test=session.execute("""Select count(*) from aoe.{} where name='{}' ALLOW FILTERING""".format((categ),request.json['name']))
    #checks if the target name is in the database
    for row in name_test:
        count_name=row.count
    
    if count_name==0 and count_id==0:
        #inserts reccord and returns 201 response
        session.execute("""INSERT into aoe.{}(id,name) values({},'{}')""".format((categ),request.json['id'],request.json['name']))
        return jsonify({'message':'created:/item id={} and name={} in table {}'.format(request.json['id'],request.json['name'],(categ))}),201
    
    else:
        #returns 400 bad request response if name or id are already in the database
        return jsonify({'message':'id number or name of item already on record.'}),400

@app.route('/list/<categ>',methods=['PUT'])
def edit_record(categ):
    """A function that is used to edit existing records on any of the category lists using a PUT curl command
    Inputs: categ -- the target category table, specified in the url given in the curl command
    Outputs: multiple outputs depending on the curl command:
        if the request in the curl command isn't in json or the request does not have a name -- returns a 400 bad request response
        if the target name is not in the database and the target id is -- returns a 200 OK response and details of the item edited.
        if the target id is not in the database --- returns a 400 bad request response
        if the target name is already in the database --- returns a 400 bad request response"""
        
    if not request.json or not 'name' in request.json:
        return jsonify({'error':'the new record to be changed must have a name and Id'}),400
    
    id_test=session.execute("""Select count(*) from aoe.{} where id={}""".format((categ),request.json['id']))
    
    for row in id_test:
        count_id=row.count
    
    name_test=session.execute("""Select count(*) from aoe.{} where name='{}' ALLOW FILTERING""".format((categ),request.json['name']))
    
    for row in name_test:
        count_name=row.count
    
    if count_name==0 and count_id==1:
        session.execute("""UPDATE aoe.{} set name='{}' where id={}""".format((categ),request.json['name'],request.json['id']))
        return jsonify({'message':'updated:name of item id={} in table {} to {}'.format(request.json['id'],(categ),request.json['name'])}),200
    
    if count_id==0:
        return jsonify({'message':'Id of item not found on record.'}),400
    
    if count_name==1:
        return jsonify({'message':'name of item already on record.'}),400
    


@app.route('/list/<categ>',methods=['DELETE'])
def delete_record(categ):
    """A function that is used to delete a record from any of the category lists using a DELETE curl command
    Inputs: categ -- the target category table, specified in the url given in the curl command
    Outputs: multiple outputs depending on the curl command:
       if the request in the curl command isn't in json or the request does not have a name -- returns a 400 bad request response
       if the target id is not on the record --- returns a 400 bad request response 
       if the target id is on record --- returns a 200 OK response and details of the item deleted.
       """
    if not request.json or not 'id' in request.json:
        return jsonify({'error':'the record to be Deleted must have an Id'}),400
    id_test=session.execute("""Select count(*) from aoe.{} where id={}""".format((categ),request.json['id']))
    for row in id_test:
        count_id=row.count
    if count_id==1:
        session.execute("""DELETE from aoe.{} where id={}""".format((categ),request.json['id']))
        return jsonify({'message':'Deleted item id={} from table {}'.format(request.json['id'],(categ))}),200
    if count_id==0:
        return jsonify({'message':'Id of item not found on record.'}),400


    
@app.route('/id/<ex_categ>/<ex_name>', methods=['GET'])
def find_id(ex_categ,ex_name):
    """A function that returns the id for a given name of asset on a given category list
    Inputs: ex_categ --- the target category list
            ex_name --- the target asset name
    Outputs:a table of one row with the asset name and id."""
    data=session.execute("""Select * From aoe.{categ} WHERE name='{name}' ALLOW FILTERING""".format(categ=ex_categ,name=ex_name))
    table = "<TABLE border='1'>"
    for row in data:
        table+="<TR><TD>" + str(row.id) +"</TD><TD>"+row.name+"</TD><TR>"
    table+="</TABLE>"
    return table, 200


@app.route('/civilization/<civ_ex_id>', methods=['GET'])
def get_civ(civ_ex_id):
    """Requests information, in json, about a given civilization (name or id) from the external api using a get request"""
    civ_url=civ_url_template.format(civ_id=civ_ex_id)
    print(civ_url)
    resp_civ = requests.get(civ_url)    
    if resp_civ.ok:
        data= resp_civ.json()
        return data, 200
    else:
        print(resp_civ.reason)

@app.route('/structure/<struc_ex_id>', methods=['GET'])
def get_struc(struc_ex_id):
    """Requests information, in json, about a given structure (name or id) from the external api using a get request"""
    struc_url=struc_url_template.format(struc_id=struc_ex_id)
    print(struc_url)
    resp_struc = requests.get(struc_url)    
    if resp_struc.ok:
        data= resp_struc.json()
        return data, 200 
    else:
        print(resp_struc.reason)

@app.route('/technology/<tech_ex_id>', methods=['GET'])
def get_tech(tech_ex_id):
    """Requests information, in json, about a given technology (name or id) from the external api using a get request"""
    tech_url=tech_url_template.format(tech_id=tech_ex_id)
    print(tech_url)
    resp_tech = requests.get(tech_url)    
    if resp_tech.ok:
        data= resp_tech.json()
        return data,200
    else:
        print(resp_tech.reason)
        
@app.route('/unit/<unit_ex_id>', methods=['GET'])
def get_unit(unit_ex_id):
    """Requests information, in json, about a unit civilization (name or id) from the external api using a get request"""
    unit_url=unit_url_template.format(unit_id=unit_ex_id)
    print(unit_url)
    resp_unit = requests.get(unit_url)    
    if resp_unit.ok:
        data= resp_unit.json()
        return data,200 
    else:
        print(resp_unit.reason)
        
    
if __name__=='__main__':
    app.run(host='0.0.0.0',port=80, debug=True)
