_ = require 'underscore'
$ = require 'jquery'

{throw_error} = require 'commons'
{log} = require 'logger'
config = require 'config'
{user} = require 'models'
{Window} = require './window'
{Signup} = require './signup'


class Login extends Window
  _template_name: 'login'

  login_facebook: ->
    current_path = location.href.replace(
      new RegExp('\\' + (location.search or '?')), ''
    )
    if $.isTouchDeveice
      location.href = "http://www.facebook.com/dialog/oauth/?" + $.param(
        client_id: config.facebook_id, redirect_uri:current_path
        scope: 'email'
      )
    else
      FB.login (->), scope: 'email'

  signup_email: ->
    new Signup().show throw_error
    

module.exports = {Login}