# Python program to implement client side of chat room.
import FSNClient
import FSNObjects
import socket
import bge
import math
import time
from uuid import getnode as get_mac
import random
logic = bge.logic
scene = logic.getCurrentScene()
utils = logic.utils
import mapLoad
def quitGame():
    print("exiting game")
    try:
        utils.getNetworkClient().quit()
    except:
        pass
    scenes = logic.getSceneList()
    currentScene = logic.getCurrentScene()
    for scene in scenes:
        if(scene!=currentScene):
            scene.end()
    utils.resetGameState()
    utils.setMode(utils.MODE_MENU)
    currentScene.replace("Menu Background")

def addNewPlayer(playerID):
    print("addNewPlayer("+str(playerID)+")")
    newObj = scene.addObject("playerQuad",logic.player,0)
    logic.peers[playerID] = newObj #lets add this new player model to a dict so we can reference it later

def removePlayer(playerID):
    try:
        print("removePlayer("+str(playerID)+")")
        logic.peers[playerID].endObject()
        del logic.peers[playerID]
    except:
        print("failed to remove player: "+str(playerID))

def sendMessage(subject,body,to,messageFrom):
    print("sending game message from server")
    logic.sendMessage(subject)

def clientMessageHandler(message):
    messageType = message[FSNObjects.MESSAGE_TYPE_KEY]
    #   ("message handler called! "+str(messageType))

    #server event
    if messageType == FSNObjects.SERVER_EVENT_TYPE_KEY:
        #print("handling server event")
        #print("message = "+str(message))
        message = FSNObjects.ServerEvent.getMessage(message)
        if(message.eventType == FSNObjects.ServerEvent.PLAYER_JOINED):
            #print("- player join event")
            addNewPlayer(message.senderID)
        if(message.eventType == FSNObjects.ServerEvent.ACK):
            utils.getNetworkClient().serverReady = True
        if(message.eventType == FSNObjects.ServerEvent.MAP_SET):
            print("we should load a map!")
            mapData = message.extra
            mapLoad.spawnMapElements(mapData)
            print("map load complete!")

    #player state
    if messageType == FSNObjects.PLAYER_STATE:
        #print("handling player state")
        #print("message = "+str(message))
        message = FSNObjects.PlayerState.getMessage(message)
        if(message.senderID in logic.peers):
            peerObject = logic.peers[message.senderID]
            peerObject.position = message.position
            peerObject.orientation = message.orientation

    #player event
    if messageType == FSNObjects.PLAYER_EVENT:
        print("handling player event")
        print("message = "+str(message))
        message = FSNObjects.PlayerEvent.getMessage(message)
        if(message.eventType == FSNObjects.PlayerEvent.PLAYER_JOINED):
            #print("- player join event")
            addNewPlayer(message.senderID)
        if(message.eventType == FSNObjects.PlayerEvent.PLAYER_QUIT):
            removePlayer(message.senderID)
        if(message.eventType == FSNObjects.PlayerEvent.PLAYER_MESSAGE):
            messageBody = None
            MessageTo = None
            MessageFrom = None
            sendMessage(message.extra,messageBody,MessageTo,MessageFrom)

    #server state
    if messageType == FSNObjects.SERVER_STATE:
        print("handling server state")
        print("message = "+str(message))
        message = FSNObjects.ServerState.getMessage(message)
        peerStates = message.playerStates
        for key in peerStates:
            if(key==utils.getNetworkClient().clientID):
                pass
            else:
                peerState = peerStates[key]
                #print(peerStates)
                message = FSNObjects.PlayerState.getMessage(peerState)
                newObj = scene.addObject("playerQuad",logic.player,0)
                print("ADDING NEW PLAYER OBJECT!!!!!")
                logic.peers[key] = newObj #lets add this new player model to a dict so we can reference it later
                #print(logic.peers)
                peerObject = logic.peers[key]
                peerObject.position = message.position
                peerObject.orientation = message.orientation

def setup():
    print("JOINING SERVER!!!")
    #
    utils.setNetworkClient(FSNClient.FSNClient(utils.getServerIP(),50001))
    utils.getNetworkClient().connect()
    playerJoinEvent = FSNObjects.PlayerEvent(FSNObjects.PlayerEvent.PLAYER_JOINED,utils.getNetworkClient().clientID)
    utils.getNetworkClient().sendEvent(playerJoinEvent)
    utils.getNetworkClient().setMessageHandler(clientMessageHandler)
    logic.peers = {}

def run():
    position = list(logic.player.position)
    o = logic.player.orientation.to_euler()
    orientation = [o[0],o[1],o[2]]
    color = [0,0,1]
    myState = FSNObjects.PlayerState(utils.getNetworkClient().clientID,None,position,orientation,color)

    utils.getNetworkClient().updateState(myState)
    utils.getNetworkClient().run()

def main():
    #if hasattr(logic, 'isSettled'):
    try:
        logic.lastNetworkTick
    except:
        logic.lastNetworkTick = 0
    try:
        logic.lastLogicTic
    except:
        logic.lastLogicTic = float(time.perf_counter())
    if utils.getNetworkClient()!=None:
        #if(logic.lastNetworkTick>=0.1):
        #if(logic.lastNetworkTick>=0.01):
        if utils.getNetworkClient().isConnected():
            run()
            logic.lastNetworkTick = 0
        else:
            quitGame()

    else:
        setup()
        logic.lastNetworkTick = 0
    lastFrameExecution = float(time.perf_counter())-logic.lastLogicTic
    logic.lastNetworkTick+=lastFrameExecution

if(utils.getMode()==utils.MODE_MULTIPLAYER):
    main()
