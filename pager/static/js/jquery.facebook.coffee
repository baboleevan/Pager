$.facebook = (id, {locale, events}={}, callback=->) ->                                  
  locale ?= 'en_US'
  events ?= {}

  window.fbAsyncInit = ->                                                       
    for event, handler of events
      FB.Event.subscribe event, handler
    FB.init appId: id, status: true, cookie: true, xfbml: true                  
    FB.Canvas.setAutoGrow()
    FB.getLoginStatus callback                                                  

  $('body').append $('<div>').attr('id', 'fb-root')                             
  $('<script>').each ->                                                         
    @id = 'facebook-jssdk'                                                      
    @async = true                                                               
    @src = "//connect.facebook.net/#{locale}/all.js"                            
    $('head').append @
