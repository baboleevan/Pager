$ = require 'jquery'
_ = require 'underscore'
{bindingHandlers} = require 'knockout'

{log} = require 'logger'
require 'ext'

class TouchEvent
  constructor: (
    @start, {
      @swipe_threadhold, @hold_threshold, holdstart, @holdcancle, @dragstart
    }
  ) ->
    # ios uses save event object
    @start = @last = pageX: @start.pageX, pageY: @start.pageY
    # total travled
    @travled = x: 0, y: 0
    # final distance
    @displacement = x: 0, y: 0
    # last movement
    @last_movement = x: 0, y: 0
    @is_hold_enought = no
    @holddown_timer_id = setTimeout =>
      @is_hold_enought = yes
      holdstart?()
    , @hold_threshold
    @is_drag = no

  push: (event) ->
    @travled.x = @travled.x + (event.pageX - @last.pageX).abs()
    @travled.y = @travled.y + (event.pageY - @last.pageY).abs()
    # 최초로 swipe_threadhold를 넘은 시점에 dragstart이벤트를 발생시킨다.
    # drag start event 발생후 dragmove가 연속으로 발생한다.
    # 이전값을 보존해서 일단 전달해서 dragstart부터 touch상태를 계속 처리한다.
    if (not @is_drag) and (Math.max(@travled.x, @travled.y) > @swipe_threadhold)
      @is_drag = yes
      @is_hold_enought = no
      @cancle_holddown yes
      # when starting event last movement is same as displacement
      @dragstart?(
        displacement: displacement, last_movement: displacement
      )
    @displacement =
      x: (event.pageX - @start.pageX), y: (event.pageY - @start.pageY)
    @last_movement = x: event.pageX - @last.pageX, y: event.pageY - @last.pageY
    @last = pageX: event.pageX, pageY: event.pageY

  is_tab: ->
    @is_hold_enought and not @is_drag

  cancle_holddown: (bubble=no)->
    if @holddown_timer_id
      clearTimeout @holddown_timer_id
      delete @holddown_timer_id 
      if bubble
        @holdcancle?()

  finalize: ->
    @cancle_holddown()


class VirualEvent
  isTouchDevice: no

  constructor: (element, {events, @swipe_threadhold, @hold_threshold}) ->
    @swipe_threadhold ?= 30 #px
    @hold_threshold ?= 50 #ms
    @events = {}
    @update_events events
    $e = $ element
    $e
      .on('touchstart', @_on_touchstart)
      .on('touchmove', @_on_touchmove)
      .on('touchend', @_on_touchend)
      .on('click', @_on_click)

    @_on_holdstart = =>
      $(element).trigger @_extend_event 'vholdstart', currentTarget: element

    @_on_holdcancle = =>
      $(element).trigger @_extend_event 'vholdcancel', currentTarget: element

    @_on_dragstart = (opts) =>
      $(element).trigger(
        @_extend_event('vdragstart', _.extend({currentTarget: element}, opts))
      )

  update_events: (events) ->
    for event in events
      @events[event] = true

  _on_touchstart: (e) =>
    @touch?.finalize()
    @isTouchDevice = yes
    opts = swipe_threadhold: @swipe_threadhold, hold_threshold: @hold_threshold
    if @events.vholdstart or @events.vholdend
      opts.holdstart = @_on_holdstart
      opts.holdcancle = @_on_holdcancle
    if @events.vdragstart or @events.vdragend
      opts.dragstart = @_on_dragstart
    @touch = new TouchEvent e.originalEvent.touches[0], opts

  _on_touchmove: (e) =>
    @touch.push (e.originalEvent ? e).touches[0]
    if @touch.is_drag
      event = _.extend(
        @_extend_event('vdragmove', e),
        displacement: @touch.displacement, last_movement: @touch.last_movement
      )
      $(e.currentTarget).trigger event

  _on_touchend: (e) =>
    # touch needs finalizing
    @touch.finalize()
    $e = $(e.currentTarget)
    prevent_default = no
    if @events.vtab and @touch.is_tab()
      $e.trigger @_extend_event 'vtab', e
      prevent_default = yes # prevent default touchend events
    if @events.vholdend and @touch.is_hold_enought
      $e.trigger @_extend_event 'vholdend', e
      prevent_default = yes
    if @events.vdragend and @touch.is_drag
      $e.trigger(
        _.extend(
          @_extend_event('vdragend', e),
          displacement: @touch.displacement, last_movement: @touch.last_movement
        )
      )
      prevent_default = yes
    if @events.vswipehorizon and @touch.is_drag
      if @touch.displacement.x.abs() > @touch.displacement.y.abs()
        $e.trigger(
          _.extend(
            @_extend_event('vswipehorizon', e),
            displacement: @touch.displacement.x
          )
        )
        prevent_default = yes

    return not prevent_default

  _on_click: (e) =>
    if not @isTouchDevice and @events.vtab
      $(e.currentTarget).trigger @_extend_event 'vtab', e

  _extend_event: (name, event, {properties}={}) ->
    properties ?= ['currentTarget']
    e = new $.Event name
    for property in properties
      e[property] = event[property]
    e

$.fn.vevent = ({events}) ->
  @each ->
    if @virual_event
      @virual_event.update_events events
    else
      @virual_event = new VirualEvent @, events: events


# simple shortcut for vevent
bindingHandlers.vtab =
  init: (element, valueAccessor, allBindingsAccessor, viewModel) ->
    newValueAccessor = ->
      {vtab: valueAccessor()}
    bindingHandlers.vevent.init.call(
      this, element, newValueAccessor, allBindingsAccessor, viewModel
    )

# activate vevent & delegate event handleing
bindingHandlers.vevent =
  init: (element, valueAccessor, allBindingsAccessor, viewModel) ->
    events = valueAccessor()
    # activate vevent
    $(element).vevent(
      events: _.keys events
    )
    return bindingHandlers.event.init.call(
      this, element, valueAccessor, allBindingsAccessor, viewModel
    )
