extensions [csv table time]

globals
[
  event-data ;data structure storing all demand events output from generator
  event-reference ;data structure storing characteristics of event types - i.e. resource requirements - to be derived in first instance from ONS crime severity scores
  count-completed-events

  ;Globals to keep track of time
  dt
  Shift-1
  Shift-2
  Shift-3

  count-crime-hour

  ;file globals
  event-summary-file
  active-event-trends-file
  active-resource-trends-file
  resource-summary-file
  resource-usage-trends-file

]

;Events store demand - the things the police muct respond to
breed [events event]

;Resource store supply the thing police use to respond to demand - each unit nominally represents a single officer
breed [resources resource]


;POLICE RESOURCE VARIABLES
resources-own
[

  current-event ;the id of the event-agent the resource-agent is responding to
  current-event-type ;the type of event the resource-agent is responding to
  current-event-class ; broader crime class

  ;placeholders to allow units of resource to only be able to respond of events of a certain type - currently not used
  resource-type
  resource-roles

  ;status of resource agent
  resource-status ;represents the current state of the resource agent - coded: 0 = off duty, 1 - on duty and available, 2 = on duty and responding to an event
  resource-start-dt ; the date-time when the current job started

  resource-hours-required ;count of hours required to respond to current event
  resource-end-dt ;calculated end date/time of current event - equates to resource-start-dt + resource-hours-required

  ;records what shift - if any - a resource is working on
  working-shift

  events-completed ;measure of total number of incidents completed

]



;DEMAND EVENT VARIABLES
events-own
[
  eventID ;link back to event data

  current-resource ; the resource agent(s) (can be multiple) - if any - currently repsonding to this event
  event-status ;status of demand event - coded 1 = awaiting supply, 2 = ongoing, 3 = completed

  event-type ;event type in this model - crime type - i.e. aggravated burglary
  event-class ;event broad class - i.e. burglary

  event-LSOA

  event-start-dt ;datetime event came in
  event-response-start-dt ;datetime response to event started
  event-response-end-dt ;when the event will be reconciled calculated once an event is assigned a resource.

  event-resource-counter ;counts the amount of time spent on an event


  event-resource-type ; placeholders to allow units of resource to only be able to respond of events of a certain type - currently not used

  event-resource-req-time ;amount of time resource required to repsond to event - drawn from event-reference
  event-resource-req-amount ;number of resource units required to repsond to event - drawn from event-reference
  event-resource-req-total

  event-priority ; placeholder for variable that allows events to be triaged in terms of importance of response

]






;Procedure to check datetime and adjust flags for shifts currently active/inactive
to check-shift

  ;Shifts:
  ;1. 0700 - 1700
  ;2. 1400 - 2400
  ;3. 2200 - 0700

  let hour time:get "hour" dt

  ;Currently no working roster-off solution - what to do when a job is ongoing?

  ;Shift 1
  if hour = 7 [ set Shift-1 TRUE roster-on 1  ]
  if hour = 17 [ set Shift-1 FALSE roster-off 1 ]

  ;Shift 2
  if hour = 14 [ set Shift-2 TRUE roster-on 2 ]
  if hour = 0 [ set Shift-2 FALSE ]

  ;Shift 3
  if hour = 22 [ set Shift-3 TRUE roster-on 3 ]
  if hour = 7 [ set Shift-3 FALSE ]

end





;main setup procedure
to setup

  ;clear stuff
  ca
  reset-ticks


  set event-summary-file (word "model-output/event-summary-file-" replication ".csv")
  set active-event-trends-file (word "model-output/active-event-trends-file-" replication ".csv")
  set active-resource-trends-file (word "model-output/active-resource-trends-file-" replication ".csv")
  set resource-summary-file (word "model-output/officer-summary-file-" replication ".csv")
  set resource-usage-trends-file (word "model-output/resource-usage-trends-file-" replication ".csv")



  ;size the view window so that 1 patch equals 1 unit of resource - world is 50 resources wide - calculate height and resize
  ;let dim-resource-temp (ceiling (sqrt number-resources)) - 1
  let dim-resource-temp (number-resources / 25) - 1

  resize-world 0 24 0 dim-resource-temp

  ;initialize shift bools
  set Shift-1 false
  set Shift-2 false
  set Shift-3 false

  ; create police resoruce agents - one per patch
  ask n-of number-resources patches
  [
    sprout-resources 1
    [
      set shape "square"
      set color grey
      ifelse Shifts [set resource-status 0] [set resource-status 1]
      set events-completed 0
    ]
  ]

  ;set the global clock


  if event-file-out [start-file-out]


  ;read in the event data
  print "Reading Event Data from file ......"

  if demand-events = "Synthetic" [ set event-data csv:from-file "input-data/fine-categories/WYP_synthetic_day_reports.csv" set dt time:create "2019/01/01 7:00" ]
  if demand-events = "Actual" [ set event-data csv:from-file "input-data/fine-categories/WYP_historic_day_reports.csv" set dt time:create "2016/03/01 7:00" ]
  set event-data remove-item 0 event-data ;remove top row

  ;read in the event reference table to assign resource charactersitics by offence
  print "Importing Event Resourcing Profiles from file ......"
  set event-reference table:make

  ;Build the dictionary from event ref file - thsi allows us to update the resourcing weighst associate with offences by editing the CSV
  if event-characteristics = "Uniform"
  [
    let event-ref-file csv:from-file "input-data/fine-categories/Activity_Times_Uniform.csv"
    foreach event-ref-file [ x -> table:put event-reference item 0 x (list item 1 x item 2 x item 3 x item 4 x) ]
    print event-ref-file
  ]
  if event-characteristics = "Experimental"
  [
    let event-ref-file csv:from-file "input-data/fine-categories/Activity_Times_Crime_Severity_Score_v1.csv"
    foreach event-ref-file [ x -> table:put event-reference item 0 x (list item 1 x item 2 x item 3 x item 4 x item 5 x) ]
    print event-ref-file
  ]

  ;print event-ref-file

end



to roster-on [ shift ]

  ;as a shift changes roster on new staff - assumes that each shift has 1/3 of resources active - although there is overlap between shifts

  print (word "Shift " shift " - Rostering on ")

  if shift = 1 [ ask n-of floor ( number-resources / 3 )  resources with [resource-status = 0] [set resource-status 1 set working-shift 1 ]]
  if shift = 2 [ ask n-of floor ( number-resources / 3 )  resources with [resource-status = 0] [set resource-status 1 set working-shift 2 ]]
  if shift = 3 [ ask n-of floor ( number-resources / 3 ) resources with [resource-status = 0] [set resource-status 1 set working-shift 3 ]]

end



;to do next - howdo we roster off officers - what happens to events that arecurrently underway - how are they passed on
; A few  options
; Pass events on to specific  other resource agents
;put the events backon the stack (this would require to count amount of time spent on event so to know remaining hours
; continue working until event finishes - this would likely require agents to pick up events based on how much  time they have lefton their shift
to roster-off [ shift ]

  if shift = 1
  [
    print (word "Shift 1 ends - currently there are " count resources with [ working-shift = 1] " working and " count resources with [resource-status = 1 and working-shift = 1] " officers not on a job to be easily rostered off")
    ask resources with [resource-status = 1 and working-shift = 1] [end-shift]
  ]
  ;if shift = 2 [ ask n-of 100 resources with [resource-status = 0] [set resource-status 1 set working-shift 2 ]]
  ;if shift = 3 [ ask n-of 100 resources with [resource-status = 0] [set resource-status 1 set working-shift 3 ]]

end



to end-shift
  set resource-status 0
  set working-shift 0
end




;the main simulation loop
to go-step

  if VERBOSE [print time:show dt "dd-MM-yyyy HH:mm"]

  ;update time and check shift bool
  if Shifts [check-shift]
  set count-crime-hour 0

  ;read in current hour's events
  read-events




  ;here we could ask resources to find events - but we do need to deal with the fact that some resources require more than one unit of resource
;  ask resources with [resource-status = 1]
;  [
;    print (word " resource: " who " looking for a job - following available:")
;      ask events [print (word "event:" who " - " event-type " - priority: " event-priority )]
;  ]






  ;assign resources - right now this is written events look for resources where in reality resources should look for events
  ifelse not triage-events
  [
    print "poo"
    ask events with [event-status = 1] [get-resources]
  ]
  [
    ;rudimentary triage
    let events-awating events with [event-status = 1]
    ask events-awating with [event-priority = 1] [get-resources]
    ask events-awating with [event-priority = 2] [get-resources]
    ask events-awating with [event-priority = 3] [get-resources]
  ]





  ;update visualisations - do this after resources have been allocated and before jobs have finished - so that plots reflect actual resource usage 'mid-hour' as it were
  ask resources [  draw-resource-status ]
  update-all-plots

  ;check status of ongoing events so those about to complete can be closed
  ask events with [event-status = 2] [ check-event-status ]

  ;tick by one hour
  increment-time

  ;repeat

end


;increment internal tick clock and date time object - 1 tick = 1 hour
to increment-time
  tick
  set dt time:plus dt 1 "hours"
end









to start-file-out

  file-close-all

  if file-exists? event-summary-file [file-delete event-summary-file]
  file-open event-summary-file
  file-print "eventID,count-resources,event-status,event-type,event-class,event-LSOA,event-start-dt,event-response-start-dt,event-response-end-dt,event-resource-counter,event-resource-type,event-resource-req-time,event-resource-req-amount,event-resource-req-total"

  if file-exists? active-event-trends-file [file-delete active-event-trends-file]
  file-open active-event-trends-file
  file-print "date-time,Anti-social behaviour,Bicycle theft,Burglary,Criminal damage and arson,Drugs,Other crime,Other theft,Possession of weapons,Public order,Robbery,Shoplifting,Theft from the person,Vehicle crime,Violence and sexual offences"

  if file-exists? active-resource-trends-file [file-delete active-resource-trends-file]
  file-open active-resource-trends-file
  file-print "date-time,Anti-social behaviour,Bicycle theft,Burglary,Criminal damage and arson,Drugs,Other crime,Other theft,Possession of weapons,Public order,Robbery,Shoplifting,Theft from the person,Vehicle crime,Violence and sexual offences"

  if file-exists? resource-usage-trends-file [file-delete resource-usage-trends-file]
  file-open resource-usage-trends-file
  file-print "date-time,usage%,events-ongoing,events-waiting,piority1-waiting,piority2-waiting,piority3-waiting"

end





; procedure to read in the events for the given time window / tick
to read-events

  ;event structure is

  ;0    1         2     3   4   5     6                     7                     8         9
  ;row  UID	      Year	Mon	Day	Hour	Crime_description	    Crime_type	          LSOA_code	Police_force
  ;0    E010111A0	2019	1	  1	  22	  Anti-social behaviour	Anti-social behaviour	E01010650	West Yorkshire


  let day-end FALSE

  while [not day-end]
  [
    ;pull the top row from the data
    let temp item 0 event-data

    ;extract hour/day/month from next event
    let tmp-event-year item 2 temp
    let tmp-event-month item 3 temp
    let tmp-event-day item 4 temp
    let tmp-event-hour item 5 temp

    ;construct a date
    let temp-dt time:create (word tmp-event-year  "-" tmp-event-month "-"  tmp-event-day " " tmp-event-hour ":00:00")

    ;check if the event occurs at current tick
    ifelse (time:is-equal temp-dt dt)
    [
      ;creat an event agent
      create-events 1
      [
        set count-crime-hour count-crime-hour + 1

        ;make it invisible
        set hidden? true

        ;fill in relevant details for event from data
        set eventID item 1 temp

        set event-type item 6 temp
        set event-class item 7 temp
        set event-LSOA item 8 temp
        set event-start-dt dt
        set event-status 1 ; awaiting resource

        ;get the amount of units/time required to respond to resource from event info
        set event-resource-req-amount get-event-resource-amount event-type
        set event-resource-req-time get-event-resource-time event-type
        set event-resource-req-total event-resource-req-amount * event-resource-req-time
        set event-resource-counter 0

        set event-priority get-event-priority event-type
      ]

      ;once the event agent has been created delete it from the data file
      set event-data remove-item 0 event-data
    ]
    [
      set day-end TRUE
      ;print "Next Day......"
      ;print data
    ]
  ]

end



; color resource agents based on current state - blue for responding - grey for available
to draw-resource-status
  if resource-status = 0 [ set color grey ] ; rostered off
  if resource-status = 1 [ set color white ] ; active & available
  if resource-status = 2 [ set color blue ] ; active & on event
end




; procedure that takes an event type and probabilistically returns how many hours it will require
to-report get-event-resource-time [ eventType ]


  ; pull the time require to adress an offence from the event-reference dictionary -
  let event-info  table:get event-reference eventType

  let mean-time item 0 event-info
  let sd-time item 1 event-info

  ;in this 'stupid' case just apply a random normal to that time to get the actual time to return - and make sure it's a positive number with ABS - HACK
  let time abs round random-normal mean-time sd-time


  ;show (word eventType " - mean-time=" mean-time " ,sd-time=" sd-time " -- Actual=" time)

 report time

end


; procedure that takes an event type and probabilistically returns how many resource agents it will require
to-report get-event-resource-amount [ eventType ]

  ; pull the mean amount of resource required to adress an event from the event-reference dictionary -
  let event-info  table:get event-reference eventType

  let mean-amount item 2 event-info
  let sd-amount item 3 event-info

  ;in this 'stupid' case just apply a random poisson to the mean ammount to get the actual amount to return - and make sure it's a positive number with ABS and at least 1 - so that all events require a resource - HACK
  let amount (round random-poisson mean-amount) + 1

  ;show (word eventType " - mean-amount=" mean-amount " ,sd-amount=" sd-amount " -- Actual=" amount)

  report amount

end


to-report get-event-priority [ eventType ]

  let event-info  table:get event-reference eventType
  let priority item 4 event-info
  report priority

end






; event procedure that checks whether a currently running event can be closed off
to check-event-status
  ;check when event being responded to should be finshed

  ;check if the secdeuled event end date/time is now
  ifelse time:is-equal event-response-end-dt dt
  [
    ; if it is this cycle - end the event, record that, relinquish resource(s), destroy the event agent
    ask current-resource [ relinquish ]
    ;count completion
    set count-completed-events count-completed-events + 1
    ;destroy event object

    ;show (word "Job complete")


    ;if the job is complete write its details to the event output file
    if event-file-out
    [
      file-open event-summary-file
      file-print (word
        eventID ","
        count current-resource ","
        event-status ",\""
        event-type "\",\""
        event-class "\","
        event-LSOA ","
        (time:show event-start-dt "dd-MM-yyyy HH:mm") ","
        (time:show event-response-start-dt "dd-MM-yyyy HH:mm")  ","
        (time:show event-response-end-dt "dd-MM-yyyy HH:mm") ","
        event-resource-counter ","
        event-resource-type ","
        event-resource-req-time ","
        event-resource-req-amount ","
        event-resource-req-total
      )
    ]

    ;then destroy the object
    die
  ]
  [
    ;otherwise count the time spent thus far
    set event-resource-counter event-resource-counter + count current-resource
    ;show (word "Job ongoing - requires = " event-resource-req-total " --- resourced " event-resource-counter " thus far")
  ]



end


;
to relinquish

  set events-completed events-completed + 1
  set resource-status 1
  set current-event-type ""
  set current-event-class ""

end





; event procedure to assess if sufficient resources are available to respond to event and if so allocate them to it
to get-resources

  ;check if the required number of resources are available
  ifelse count resources with [resource-status = 1] >= event-resource-req-amount
  [

    if VERBOSE [print (word "Officers responding to " event-type " event - " event-resource-req-amount " unit(s) required for " event-resource-req-time " hour(s) - TOTAL RESOURCE REQ = " event-resource-req-total)]

    ;link resource to event
    set current-resource n-of event-resource-req-amount resources with [resource-status = 1]

    ;record start and end datetime of response
    set event-response-start-dt dt
    set event-response-end-dt time:plus dt (event-resource-req-time) "hours"
    set event-status 2 ; mark the event as ongoing

    ask current-resource
    [
      ;link event to resource
      set current-event myself
      set current-event-type [event-type] of current-event
      set current-event-class [event-class] of current-event
      set resource-status 2
      set resource-start-dt dt
      set resource-hours-required [event-resource-req-time] of current-event
      set resource-end-dt [event-response-end-dt] of current-event

      set color blue
    ]
  ]
  [
    ;print "Insuffiecient resources available for event .... waiting ...."
  ]




end






;plot update commands
to update-all-plots



  file-open resource-usage-trends-file
  file-print (word (time:show dt "dd-MM-yyyy HH:mm") "," ((count resources with [resource-status = 2] / count resources with [resource-status = 2 or resource-status = 1] ) * 100) "," (count events with [event-status = 2]) "," (count events with [event-status = 1]) "," (count events with [event-status = 1 and event-priority = 1]) "," (count events with [event-status = 1 and event-priority = 2]) "," (count events with [event-status = 1 and event-priority = 3]))





  set-current-plot "Crime"
  set-current-plot-pen "total"
  plot count-crime-hour

  set-current-plot "Total Resource Usage"
  set-current-plot-pen "Supply"
  plot (count resources with [resource-status = 2] / count resources with [resource-status = 2 or resource-status = 1] ) * 100

  set-current-plot "Events Waiting"
  set-current-plot-pen "waiting-total"
  plot count events with [event-status = 1]
  set-current-plot-pen "waiting-1"
  plot count events with [event-status = 1 and event-priority = 1]
  set-current-plot-pen "waiting-2"
  plot count events with [event-status = 1 and event-priority = 2]
  set-current-plot-pen "waiting-3"
  plot count events with [event-status = 1 and event-priority = 3]


  ;------------------------------------------------------------------------------------------------------------------------------

  ;plotting and recording the amount of events currently being responded to by crime-classes this hour
  set-current-plot "active-events"
  file-open active-event-trends-file
  ;only look at active events
  let current-events events with [event-status = 2]
  let out-string (word (time:show dt "dd-MM-yyyy HH:mm") ",")

  set-current-plot-pen "Anti-social behaviour"
  let x count current-events with [event-class = "Anti-social behaviour"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Bicycle theft"
  set x count current-events with [event-class = "Bicycle theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Burglary"
  set x count current-events with [event-class = "Burglary"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Criminal damage and arson"
  set x count current-events with [event-class = "Criminal damage and arson"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Drugs"
  set x count current-events with [event-class = "Drugs"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other crime"
  set x count current-events with [event-class = "Other crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other theft"
  set x count current-events with [event-class = "Other theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Possession of weapons"
  set x count current-events with [event-class = "Possession of weapons"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Public order"
  set x count current-events with [event-class = "Public order"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Robbery"
  set x count current-events with [event-class = "Robbery"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Shoplifting"
  set x count current-events with [event-class = "Shoplifting"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Theft from the person"
  set x count current-events with [event-class = "Theft from the person"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Vehicle crime"
  set x count current-events with [event-class = "Vehicle crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Violence and sexual offences"
  set x count current-events with [event-class = "Violence and sexual offences"]
  plot x
  set out-string (word out-string x)

  file-print out-string


  ;------------------------------------------------------------------------------------------------------------------------------

  ;plotting and recording the amount of resources devoted to crime-classes this hour
  set-current-plot "resources"
  file-open active-resource-trends-file
  set out-string (word (time:show dt "dd-MM-yyyy HH:mm") ",")

  set-current-plot-pen "Anti-social behaviour"
  set x count resources with [current-event-class = "Anti-social behaviour"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Bicycle theft"
  set x count resources with [current-event-class = "Bicycle theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Burglary"
  set x count resources with [current-event-class = "Burglary"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Criminal damage and arson"
  set x count resources with [current-event-class = "Criminal damage and arson"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Drugs"
  set x count resources with [current-event-class = "Drugs"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other crime"
  set x count resources with [current-event-class = "Other crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other theft"
  set x count resources with [current-event-class = "Other theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Possession of weapons"
  set x count resources with [current-event-class = "Possession of weapons"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Public order"
  set x count resources with [current-event-class = "Public order"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Robbery"
  set x count resources with [current-event-class = "Robbery"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Shoplifting"
  set x count resources with [current-event-class = "Shoplifting"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Theft from the person"
  set x count resources with [current-event-class = "Theft from the person"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Vehicle crime"
  set x count resources with [current-event-class = "Vehicle crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Violence and sexual offences"
  set x count resources with [current-event-class = "Violence and sexual offences"]
  plot x
  set out-string (word out-string x)

  file-print out-string

  ;--------------------------------------------------------------------------------------------------------------------------------------------

  set-current-plot "scatter"
  ;clear-plot
  set-current-plot-pen "Anti-social behaviour"
  plotxy (count events with [event-class = "Anti-social behaviour" and event-status = 2]) (count resources with [current-event-class = "Anti-social behaviour"])
  set-current-plot-pen "Bicycle theft"
  plotxy (count events with [event-class = "Bicycle theft" and event-status = 2]) (count resources with [current-event-class = "Bicycle theft"])
  set-current-plot-pen "Burglary"
  plotxy (count events with [event-class = "Burglary" and event-status = 2]) (count resources with [current-event-class = "Burglary"])
  set-current-plot-pen "Criminal damage and arson"
  plotxy (count events with [event-class = "Criminal damage and arson" and event-status = 2]) (count resources with [current-event-class = "Criminal damage and arson"])
  set-current-plot-pen "Drugs"
  plotxy (count events with [event-class = "Drugs" and event-status = 2]) (count resources with [current-event-class = "Drugs"])
  set-current-plot-pen "Other crime"
  plotxy (count events with [event-class = "Other crime" and event-status = 2]) (count resources with [current-event-class = "Other crime"])
  set-current-plot-pen "Other theft"
  plotxy (count events with [event-class = "Other theft" and event-status = 2]) (count resources with [current-event-class = "Other theft"])
  set-current-plot-pen "Possession of weapons"
  plotxy (count events with [event-class = "Possession of weapons" and event-status = 2]) (count resources with [current-event-class = "Possession of weapons"])
  set-current-plot-pen "Public order"
  plotxy (count events with [event-class = "Public order" and event-status = 2]) (count resources with [current-event-class = "Public order"])
  set-current-plot-pen "Robbery"
  plotxy (count events with [event-class = "Robbery" and event-status = 2]) (count resources with [current-event-class = "Robbery"])
  set-current-plot-pen "Shoplifting"
  plotxy (count events with [event-class = "Shoplifting" and event-status = 2]) (count resources with [current-event-class = "Shoplifting"])
  set-current-plot-pen "Theft from the person"
  plotxy (count events with [event-class = "Theft from the person" and event-status = 2]) (count resources with [current-event-class = "Theft from the person"])
  set-current-plot-pen "Vehicle crime"
  plotxy (count events with [event-class = "Vehicle crime" and event-status = 2]) (count resources with [current-event-class = "Vehicle crime"])
  set-current-plot-pen "Violence and sexual offences"
  plotxy (count events with [event-class = "Violence and sexual offences" and event-status = 2]) (count resources with [current-event-class = "Violence and sexual offences"])

end




;Anti-social behaviour
;plot count events with [event-type = "Anti-social behaviour"]
;Bicycle theft
;plot count events with [event-type = "Bicycle theft"]
;Burglary
;plot count events with [event-type = "Burglary"]
;Criminal damage and arson
;plot count events with [event-type = "Criminal damage and arson"]
;Drugs
;plot count events with [event-type = "Drugs"]
;Other crime
;plot count events with [event-type = "Other crime"]
;Other theft
;plot count events with [event-type = "Other theft"]
;Possession of weapons
;plot count events with [event-type = "Possession of weapons"]
;Public order
;plot count events with [event-type = "Public order"]
;Robbery
;plot count events with [event-type = "Robbery"]
;Shoplifting
;plot count events with [event-type = "Shoplifting"]
;Theft from the person
;plot count events with [event-type = "Theft from the person"]
;Vehicle crime
;plot count events with [event-type = "Vehicle crime"]
;Violence and sexual offences
;plot count events with [event-type = "Violence and sexual offences"]









;if event-type = "Anti-social behaviour"
;if event-type = "Bicycle theft"
;if event-type = "Burglary"
;if event-type = "Criminal damage and arson"
;if event-type = "Drugs"
;if event-type = "Other crime"
;if event-type = "Other theft"
;if event-type = "Possession of weapons"
;if event-type = "Public order"
;if event-type = "Robbery"
;if event-type = "Shoplifting"
;if event-type = "Theft from the person"
;if event-type = "Vehicle crime"
;if event-type = "Violence and sexual offences"
;
;
;plot count events with [event-type = "Anti-social behaviour"]
;plot count events with [event-type = "Bicycle theft"]
;plot count events with [event-type = "Burglary"]
;plot count events with [event-type = "Criminal damage and arson"]
;plot count events with [event-type = "Drugs"]
;plot count events with [event-type = "Other crime"]
;plot count events with [event-type = "Other theft"]
;plot count events with [event-type = "Possession of weapons"]
;plot count events with [event-type = "Public order"]
;plot count events with [event-type = "Robbery"]
;plot count events with [event-type = "Shoplifting"]
;plot count events with [event-type = "Theft from the person"]
;plot count events with [event-type = "Vehicle crime"]
;plot count events with [event-type = "Violence and sexual offences"]
@#$#@#$#@
GRAPHICS-WINDOW
185
15
391
126
-1
-1
7.93
1
10
1
1
1
0
1
1
1
0
24
0
12
0
0
1
ticks
30.0

BUTTON
10
15
80
48
NIL
setup\n
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

SLIDER
10
195
175
228
number-resources
number-resources
25
5000
325.0
25
1
NIL
HORIZONTAL

BUTTON
85
15
175
48
NIL
go-step
T
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
695
15
805
60
Resources Free
count resources with [resource-status = 1]
17
1
11

MONITOR
996
15
1130
60
Events - Awaiting
count events with [event-status = 1]
17
1
11

MONITOR
1141
15
1278
60
Events - Ongoing
count events with [event-status = 2]
17
1
11

MONITOR
1290
15
1429
60
Events - Completed
count-completed-events
17
1
11

PLOT
770
65
1150
254
Total Resource Usage
time
%
0.0
10.0
0.0
100.0
true
false
"" ""
PENS
"Supply" 1.0 0 -16777216 true "" ""

PLOT
405
259
1150
518
active-events
time
count of events
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Anti-social behaviour" 1.0 0 -16777216 true "" ""
"Bicycle theft" 1.0 0 -7500403 true "" ""
"Burglary" 1.0 0 -2674135 true "" ""
"Criminal damage and arson" 1.0 0 -955883 true "" ""
"Drugs" 1.0 0 -6459832 true "" ""
"Other crime" 1.0 0 -1184463 true "" ""
"Other theft" 1.0 0 -10899396 true "" ""
"Possession of weapons" 1.0 0 -13840069 true "" ""
"Public order" 1.0 0 -14835848 true "" ""
"Robbery" 1.0 0 -11221820 true "" ""
"Shoplifting" 1.0 0 -13791810 true "" ""
"Theft from the person" 1.0 0 -13345367 true "" ""
"Vehicle crime" 1.0 0 -8630108 true "" ""
"Violence and sexual offences" 1.0 0 -5825686 true "" ""

BUTTON
85
50
175
83
NIL
go-step
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

TEXTBOX
15
625
140
702
Shifts:\n1. 0700 - 1700\n2. 1400 - 2400\n3. 2200 - 0700
15
0.0
1

MONITOR
405
15
544
60
Current DateTime
time:show dt \"dd-MM-yyyy HH:mm\"
17
1
11

PLOT
1155
259
1670
779
scatter
count events
count resource
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Anti-social behaviour" 1.0 2 -16777216 true "" ""
"Bicycle theft" 1.0 2 -7500403 true "" ""
"Burglary" 1.0 2 -2674135 true "" ""
"Criminal damage and arson" 1.0 2 -955883 true "" ""
"Drugs" 1.0 2 -6459832 true "" ""
"Other crime" 1.0 2 -1184463 true "" ""
"Other theft" 1.0 2 -10899396 true "" ""
"Possession of weapons" 1.0 2 -13840069 true "" ""
"Public order" 1.0 2 -14835848 true "" ""
"Robbery" 1.0 2 -11221820 true "" ""
"Shoplifting" 1.0 2 -13791810 true "" ""
"Theft from the person" 1.0 2 -13345367 true "" ""
"Vehicle crime" 1.0 2 -8630108 true "" ""
"Violence and sexual offences" 1.0 2 -5825686 true "" ""

PLOT
406
525
1151
782
resources
time
resources
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"Anti-social behaviour" 1.0 0 -16777216 true "" ""
"Bicycle theft" 1.0 0 -7500403 true "" ""
"Burglary" 1.0 0 -2674135 true "" ""
"Criminal damage and arson" 1.0 0 -955883 true "" ""
"Drugs" 1.0 0 -6459832 true "" ""
"Other crime" 1.0 0 -1184463 true "" ""
"Other theft" 1.0 0 -10899396 true "" ""
"Possession of weapons" 1.0 0 -13840069 true "" ""
"Public order" 1.0 0 -14835848 true "" ""
"Robbery" 1.0 0 -11221820 true "" ""
"Shoplifting" 1.0 0 -13791810 true "" ""
"Theft from the person" 1.0 0 -13345367 true "" ""
"Vehicle crime" 1.0 0 -8630108 true "" ""
"Violence and sexual offences" 1.0 0 -5825686 true "" ""

SWITCH
10
550
175
583
VERBOSE
VERBOSE
1
1
-1000

MONITOR
814
15
963
60
Resources Responding
count resources with [resource-status = 2]
17
1
11

SWITCH
10
330
175
363
Shifts
Shifts
1
1
-1000

MONITOR
550
15
690
60
Events in Queue
length event-data
17
1
11

PLOT
1156
64
1489
254
Events Waiting
NIL
NIL
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"waiting-total" 1.0 0 -16777216 true "" ""
"waiting-1" 1.0 0 -2674135 true "" ""
"waiting-2" 1.0 0 -955883 true "" ""
"waiting-3" 1.0 0 -1184463 true "" ""

SWITCH
10
585
175
618
event-file-out
event-file-out
0
1
-1000

CHOOSER
10
85
175
130
demand-events
demand-events
"Synthetic" "Actual"
1

CHOOSER
10
130
175
175
event-characteristics
event-characteristics
"Uniform" "Experimental"
1

BUTTON
10
460
302
493
NIL
ask resources \n[\nshow current-event-type\n]
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

SWITCH
10
365
175
398
triage-events
triage-events
0
1
-1000

MONITOR
1495
65
1612
110
priority 1 waiting
count events with [event-status = 1 and event-priority = 1]
17
1
11

MONITOR
1495
115
1612
160
priority 2 waiting
count events with [event-status = 1 and event-priority = 2]
17
1
11

MONITOR
1495
165
1612
210
priority 3 waiting
count events with [event-status = 1 and event-priority = 3]
17
1
11

PLOT
405
65
765
255
Crime
NIL
NIL
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"total" 1.0 0 -16777216 true "" ""

BUTTON
15
715
390
748
close files
if file-exists? resource-summary-file [file-delete resource-summary-file]\nfile-open resource-summary-file\nfile-print \"resourceID, events-completed\"\nask resources \n[\nfile-print (word who \",\" events-completed)\n]\n\nfile-close-all
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
1435
15
1595
60
NIL
mean [events-completed] of resources
1
1
11

SLIDER
360
260
397
406
replication
replication
1
100
1.0
1
1
NIL
VERTICAL

@#$#@#$#@
## WHAT IS IT?

(a general understanding of what the model is trying to show or explain)

## HOW IT WORKS

(what rules the agents use to create the overall behavior of the model)

## HOW TO USE IT

(how to use the model, including a description of each of the items in the Interface tab)

## THINGS TO NOTICE

(suggested things for the user to notice while running the model)

## THINGS TO TRY

(suggested things for the user to try to do (move sliders, switches, etc.) with the model)

## EXTENDING THE MODEL

(suggested things to add or change in the Code tab to make the model more complicated, detailed, accurate, etc.)

## NETLOGO FEATURES

(interesting or unusual features of NetLogo that the model uses, particularly in the Code tab; or where workarounds were needed for missing features)

## RELATED MODELS

(models in the NetLogo Models Library and elsewhere which are of related interest)

## CREDITS AND REFERENCES

(a reference to the model's URL on the web if it has one, as well as any other necessary credits, citations, and links)
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.1.0
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
1
@#$#@#$#@
