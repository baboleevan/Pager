io = require 'socket.io'
_ = require 'underscore'
{observable} = require 'knockout'

{log} = require 'logger'
{user} = require 'models'

socket = io.connect()
# physical connect of socket
socket.connected = observable no
# after successful authenticateion
socket.accessible = observable no

socket.on 'connect', ->
  socket.connected yes
  if user.connected()
    if user.type() is 'facebook'
      socket.authenticate_facebook user.facebook()

socket.on 'disconnect', ->
  socket.accessible no
  socket.connected no

socket.authenticate_facebook = (facebook) ->
  if socket.connected() and facebook
    await socket.emit 'authenticate facebook', facebook, defer err, response
    throw err if err
    if response
      user.connect 'facebook', response.id, response.nickname, response.email,
        response.facebook_account
      socket.accessible yes
      return
  # 연결되어 있지 않거나, 인증에 실패 하였을 경우 로그아웃 해 버린다.
  user.disconnect()
user.facebook.subscribe socket.authenticate_facebook

user.connected.subscribe (connected) ->
  if not connected
    socket.emit 'unauthenticate'
    socket.accessible no

module.exports = {socket}
