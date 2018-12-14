#!/usr/bin/python

import requests
import time
import pymysql.cursors
import pymysql
import socket
import sys

# Robot System Design 2018 - SDU
# API of the project's MES System
# Carlos, Caroline, Daniel

# Global variables
longest_order = 0
largest_order = 0
lowest_order = 100
lo_id = 0
la_id = 0
lw_id = 0
slowest = 0
fastest = 0
global_score = int()
_nCycles = int()
_orderCorrect = 1
points = int()
max_time = 0
min_time = 100
accumulated_time = 0
total_blue = 0
total_red = 0
total_yellow = 0
_nStopped = 0
_nRejected = 0


# Print current timestamp
def get_time(stcode):
    tBody = "On " + time.strftime("%c") + " - Status code = " + str(stcode)
    return tBody

# Get order list (GET)
def get_events(_url, evp):
    g_url = _url + evp
    return requests.get(g_url)

# Get order list (GET)
def get_orders(_url, path):
    g_url = _url + path
    return requests.get(g_url)

# Get single order (GET)
def get_single(_url, path, s):
    _ids = '/' + str(s)
    gs_url = _url + path + _ids
    return requests.get(gs_url)

# Take order (PUT)
def put_order(_url, path, x):
    _idx = '/' + str(x)
    pt_url = _url + path + _idx
    return requests.put(pt_url) 

# Sleeping 
def die(secs):
    time.sleep(secs)

# Get ticket from database
def get_ticket(_id):
    # Connect to database
    conn = pymysql.connect(host='localhost',
                           user='rsd',
                           password='rsd2018',
                           db='rsd2018',
                           charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)
    
    try:
        with conn.cursor() as cursor:
            # Select ticket 
            select_stmt = "select id, ticket from rsd2018.jobs where id = %s"
            cursor.execute(select_stmt, _id)
            result = cursor.fetchone()
    finally:
            # Close connection
        conn.close()
    
    return result

# Log system state (POST)
def post_log(_url, path, cid, cmnt, evt):
    log = {"cell_id": cid, "comment": cmnt, "event": evt}
    print ("Posted new log entry:")
    print ("  >> cell_id: " + str(cid))
    print ("  >> event: " + evt)
    print ("  >> cmnt: " + cmnt)
    pst_url = _url + path
    return requests.post(pst_url, json=log)

# Delete an order (DELETE)
def delete_order(_url, path, id, ticket):
    body = {"ticket":ticket}
    _idd = '/' + str(id)
    d_url = _url + path + _idd
    return requests.delete(d_url, json=body)


# Keep up the score and statistics
def count_points(red, blue, yellow, box, chrono, _id):
    
    # Save Statistics
    global points
    global longest_order
    global accumulated_time
    global total_blue
    global total_red
    global total_yellow
    global max_time
    global min_time
    global lo_id
    global slowest
    global fastest
    global largest_order
    global la_id
    global lowest_order
    global lw_id
    
    # Save timing
    accumulated_time = accumulated_time + chrono
    if chrono > max_time:
        max_time = chrono
        slowest = _id
        print("New record of slowest packaging")
    else:
        max_time = max_time
        slowest = slowest
    
    if chrono < min_time:
        min_time = chrono
        fastest = _id
        print("New record of fastest packaging")
    else:
        min_time = min_time
        fastest = fastest
        
    # Save brick count
    total_blue = total_blue + blue
    total_red = total_red + red
    total_yellow = total_yellow + yellow
    nBricks = yellow + blue + red
    if nBricks > longest_order:
        longest_order = nBricks
        lo_id = _id
        print("New record of largest order")
    else:
        longest_order = longest_order
        lo_id = lo_id
        
    add = blue*1 + red*3 + yellow*5 + box*2    
        
    if add > largest_order:
        largest_order = add
        la_id = _id
        print("New record of highest scoring order")
    else:
        largest_order = largest_order
        la_id = la_id
    
    if add < lowest_order:
        lowest_order = add
        lw_id = _id
        print("New record of lowest scoring order")
    else:
        lowest_order = lowest_order
        lw_id = lw_id
    
    # Set the final score
    if chrono <= 60:
        points = points + add
        return add
    else:
        add = add - 10
        points = points + add
        return add


# PLC communication during the processing of the order
def plc_control(sock, _plc, events, _url, _path, cid, cmt):
    
    # Instance to global score
    global global_score
    global _orderCorrect
    
    
    # Prepair data
    d = str(_plc[0]) + ',' + str(_plc[1]) + ',' + str(_plc[2])
    print ("Sending the order over socket: " + d)
    data = d.encode()

    # Send data
    sock.send(data)
    print ("Sent order data to PLC.")

    # Listen to updates in the system status. Wait until order is complete and PLC sends PML_Complete
    while True:
        rs = sock.recv(1024)
        if rs != None:
            rec = rs.decode()
            print ("Server's reply: " + str(rec))
            if str(rec) == 'ok':
                _orderCorrect = 1
                print ("The server received the order correctly.")
                print ("Waiting for updates...")
                while True:
                    rcpt = sock.recv(1024)
                    _state = rcpt.decode()
                    if int(_state) == 2:
                        print ("Server's reply: " + _state)
                        print ("PackML state update: " + events[int(_state)])
                        global_score = global_score + 1
                        break
                    elif int(_state) == 6:
                        _orderCorrect = 23
                        print ("Server's reply: " + _state)
                        print ("PackML state update: " + events[int(_state)])
                        break
                    else:
                        if((int(_state)>=0 and int(_state)<2) or (int(_state)>=3 and int(_state)<6)): 
                            print ("Server's reply: " + _state)
                            print ("PackML state update: " + events[int(_state)])
                            evt = events[int(_state)]
                            post_log(_url, _path, cid, cmt, evt)
                        
                        else:
                            print ("Server's reply: " + _state)
                    
                break
            
            else:
                print ("Server's reply: " + str(rec))
                print ("An error ocurred while sending the order. Re-sending...")
                _orderCorrect = -1
                #plc_control(sock, _plc, events, _url, _path, cid, cmt)
                break
        else:
            print ("Did not receive anything after sending the order")    
    

class manager:

    def __init__(self, cid):
        self.workcell = cid
        print("\n")
        print ("##################################")
        print ("##  WORKCELL #" + str(cid) + " ONLINE MANAGER  ##")
        print ("################################## \n")
    
    def __del__(self):
        global global_score
        global _nCycles
        global _nStopped
        global _nRejected
        global points
        global accumulated_time
        global total_blue
        global total_red
        global total_yellow
        global max_time
        global min_time
        global longest_order
        global lo_id
        global slowest
        global fastest
        global largest_order
        global la_id
        global lowest_order
        global lw_id
        
        avg_time = accumulated_time/global_score
        minn = "{0:.2f}".format(min_time)
        maxx = "{0:.2f}".format(max_time)
        avgg = "{0:.2f}".format(avg_time)
        ft = get_time(9)
        
        file = open("stats.txt","w")
        file.write("The system was stopped " + ft + "\n")
        file.write("Total number of cycles: " + str(_nCycles) + "\n")
        file.write("\n")
        file.write("PACKAGING:\n")
        file.write("\n")
        file.write("Total number of packed boxes: " + str(global_score) + "\n")
        file.write("Total score: " + str(points) + "\n")
        file.write("Total number of packed blue bricks: " + str(total_blue) + "\n")
        file.write("Total number of packed red bricks: " + str(total_red) + "\n")
        file.write("Total number of packed yellow: " + str(total_yellow) + "\n")
        file.write("Largest order packed: \n")
        file.write("  >> id: " + str(lo_id) + "\n")
        file.write("  >> Amount of bricks: " + str(longest_order) + "\n")
        file.write("Order with the highest score: \n")
        file.write("  >> id: " + str(la_id) + "\n")
        file.write("  >> Amount of bricks: " + str(largest_order) + "\n")
        file.write("Order with the lowest score: \n")
        file.write("  >> id: " + str(lw_id) + "\n")
        file.write("  >> Amount of bricks: " + str(lowest_order) + "\n")
        file.write("\n")
        file.write("OPERATING SPEED:\n")
        file.write("\n")
        file.write("Fastest order packed: \n")
        file.write("  >> id: " + str(fastest) + "\n")
        file.write("  >> Time: " + str(minn) + " seconds \n")
        file.write("Slowest order packed: \n")
        file.write("  >> id: " + str(slowest) + "\n")
        if max_time <= 60:
            file.write("  >> Time: " + str(maxx) + " seconds \n")
        else:
            in_minutes = max_time/60
            p = "{0:.2f}".format(in_minutes)
            file.write("  >> Time: " + str(p) + " minutes \n")
        
        file.write("Average time used to pack orders: " + str(avgg) + " seconds \n")
        file.write("\n")
        file.write("INTERRUPTIONS:\n")
        file.write("\n")
        file.write("Times the system was stopped: " + str(_nStopped) + "\n")
        file.write("Number of rejected orders: " + str(_nRejected) + "\n")
        file.write("\n")
        file.write("WorkCell #" + str(self.workcell) + " shutdown \n")
        file.close()