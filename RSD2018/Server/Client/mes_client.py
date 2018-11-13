#!/usr/bin/python

import mes_api


# Robot System Design 2018 - SDU
# REST API Client of the project's MES System

print "##################################"
print "##  WORKCELL #3 ONLINE MANAGER  ##"
print "################################## \n"

# Define url and paths
_url = 'http://localhost:5000'
_log = '/log'
_orders = '/orders'
_events = '/event_types'

# Define global variables
cell_id = 3
events_dict = {0:'PML_Idle', 1:'PML_Execute', 2:'PML_Complete', 3:'PML_Held', 4:'PML_Suspended', 5:'PML_Aborted', 6:'PML_Stopped', 7:'Order_Start', 8:'Order_Done'}

#mysql = MySQL()

while True:
    print "Connecting to server on " + _url + " and waiting for new jobs \n"
    # 1. Call GET method to see list of available jobs
    resp = mes_api.get_orders(_url, _orders)
    if resp.status_code != 200:
        print "Raised API Error on GET request. Status code " + str(resp.status_code)
    else:
        print "GET request " + _url + _orders + " succesful"
        mes_api.get_time(resp.status_code) 

        # Create JSON object
        jsonObj = resp.json()
    
        # Check & Print JSON object array length
        lgth = len(jsonObj['orders'])
        #print "  >> JSON object length = " + str(lgth) + "\n"

        # Seek for orders with status == ready
        for i in range(0, lgth):
            if jsonObj['orders'][i]['status'] == 'ready':
                _id = jsonObj['orders'][i]['id']
                print "Taking order #" + str(_id)
                print "Updated order with id: " + str(_id)
                print "Preparing LEGO bricks:"
                print "  >> Blue: " + str(jsonObj['orders'][i]['blue'])
                print "  >> Red: " + str(jsonObj['orders'][i]['red'])
                print "  >> Yellow: " + str(jsonObj['orders'][i]['yellow'])
                print "\n"
                break

        # Call PUT method to take an order
        r = mes_api.put_order(_url, _orders, _id)
        if r.status_code != 200:
            print "Raised API Error on PUT request. Status code " + str(r.status_code)
        else:
            print "PUT request " + _url + _orders + " succesful"
            mes_api.get_time(r.status_code)

            ticket = mes_api.get_ticket(_id)
           
            print "Order " + str(_id) + " ticket: " + str(ticket) + "\n"

            # Call GET method to see 
            r2 = mes_api.get_single(_url, _orders, _id)
            if r2.status_code != 200:
                print "Raised API Error on GET. Status code " + str(r2.status_code)
            else:
                print "GET request " + _url + _orders + " succesful"
                mes_api.get_time(r2.status_code)

                # Call POST method to add new log entry on Order_Start
                _idstr = str(_id)
                cmnt = str(ticket)
                r3 = mes_api.post_log(_url, _log, cell_id, cmnt, events_dict[7])
                if r3.status_code != 200:
                    print "Raised API Error on POST request. Status code " + str(r3.status_code)
                else:
                    print "POST request " + _url + _orders + " succesful"
                    mes_api.get_time(r3.status_code)


                #####     Order processing      #####
                #                                   #
                #                                   #        
                #                                   #        
                #                                   #        
                #                                   #        
                #                                   #        
                #                                   #        
                ##### PackML related code here  #####

    # Let's increse suspense
    print "Processing order..."
    mes_api.die(15)

    # DELETE completed order
    resp = mes_api.delete_order(_url, _orders, _id)
    if resp.status_code != 200:
        print "Raised API Error on DELETE request. Status code " + str(resp.status_code)
    else:
        print "DELETE request " + _url + _orders + " succesful"
        mes_api.get_time(resp.status_code) 

        # Log entry indicating deletion of the complete order
        r4 = mes_api.post_log(_url, _log, cell_id, cmnt, events_dict[8])
        if r4.status_code != 200:
            print "Raised API Error on POST request. Status code " + str(r4.status_code)
        else:
            print "POST request " + _url + _orders + " succesful"
            mes_api.get_time(r4.status_code)
            print "\n"


# Never ending loop