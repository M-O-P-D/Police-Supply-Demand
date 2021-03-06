extensions [csv table time pathdir py]

globals
[
  count-completed-events

  ;Globals to keep track of time
  dt ;start date-time of current timestep
  end-dt ;end date-time of the current timestep

  timestep-length-minutes ; the timestep length in minutes - i.e. 1 tick in model time is equivalent to ...

  shift-1
  shift-2
  shift-3

  count-crime-timestep  ;a count of crimes occurring in the current timestep

  CID-officers
  RESPONSE-officers

  ;file globals
  event-summary-file
  active-event-trends-file
  active-resource-trends-file
  resource-summary-file
  resource-usage-trends-file


  ; ENUMERATIONS
  ; event-status: status of demand event - coded 1 = awaiting supply, 2 = ongoing, 3 = paused
  AWAITING-SUPPLY
  ONGOING
  PAUSED

  ; resource-status - 0 = off duty, 1 - on duty and available, 2 = on duty and responding to an event
  OFF-DUTY
  ON-DUTY-AVAILABLE
  ON-DUTY-RESPONDING

  ; resource-type
  RESPONSE
  CID


  ;globals for counting current demand by offence type & non-crime
  asb-demand ;if event-type = "Anti-social behaviour"
  bike-demand ;if event-type = "Bicycle theft"
  burg-demand ;if event-type = "Burglary"
  damage-demand;if event-type = "Criminal damage and arson"
  drug-demand;if event-type = "Drugs"
  other-demand;if event-type = "Other crime"
  theft-demand;if event-type = "Other theft"
  weapons-demand;if event-type = "Possession of weapons"
  po-demand;if event-type = "Public order"
  robb-demand;if event-type = "Robbery"
  shop-demand;if event-type = "Shoplifting"
  tfp-demand;if event-type = "Theft from the person"
  veh-demand;if event-type = "Vehicle crime"
  viol-sex-demand;if event-type = "Violence and sexual offences"
  crime-demand
  non-crime-demand

]


;Events store demand - the things the police must respond to
breed [events event]

;Resource store supply the thing police use to respond to demand - each unit nominally represents a single officer
breed [resources resource]


;POLICE RESOURCE VARIABLES
resources-own
[
  current-event ;the id of the event-agent(s) the resource-agent is responding to - FOR CID this can be multiple events in parallel

  ;split resource agents into Response and CID pools, see enumeration declared in globals
  resource-type

  ;status of resource agent
  resource-status ;represents the current state of the resource agent, see enumeration declared in globals

  ;records what shift a resource is working on
  working-shift
  events-completed ;measure of total number of incidents completed

  ;towards parallel processing of jobs by single agents - i.e. an officer can be responding to 2 incidents at the same time - this is beacuse much of the demand will be associated with investigations.
  ; should this functionality only apply to CID???? Speak to Lee
  ; TODO just use len(current-event)?
  ;workload ; count the number of ongoing jobs an officer is dealing with currently - only used for CID
  max-resource-capacity ; expressed as float (0-1) representing a % so that jobs can be split across an individual - allows user to set that all officers spend x% of time doing something else
]



;DEMAND EVENT VARIABLES
events-own
[
  ; event characteristics as passed by crims
  eventID ;link back to event data
  event-type ;event type in this model - crime type - i.e. aggravated burglary
  event-class ;event broad class - i.e. burglary
  event-MSOA
  event-start-dt ;datetime event came in
  event-severity ; ONS CSS associated with offence
  event-suspect ; bool for presence of suspect

  event-resource-type ; split RESPONSE and CID events
  current-resource ; the resource agent(s) (can be multiple) - if any - currently responding to this event

  event-status ;status of demand event - coded 1 = awaiting supply, 2 = ongoing
  event-response-start-dt ;datetime response to event started
  event-resource-counter ;counts the amount of resource hours remaining before an event is finished

  event-resource-req-hours ;amount of time resource required to respond to event
  event-resource-req-officers ;number of resource units required to respond to event
  event-resource-req-total

  event-priority ; variable that allows events to be triaged in terms of importance of response


  event-requires-CID? ; bool for if event requires CID - flag to initial event as CID requirement can either be specified through expert elicited list or as a function of severity > x.

]


to set-enumerations

  ; resource-status
  set OFF-DUTY 0
  set ON-DUTY-AVAILABLE 1
  set ON-DUTY-RESPONDING 2

  ; event-status
  set AWAITING-SUPPLY 1
  set ONGOING 2
  set PAUSED 3

  ; resource-type
  set RESPONSE 1
  set CID 2

end


to reset-demand-globals
  set viol-sex-demand 0
  set asb-demand 0
  set bike-demand 0
  set burg-demand 0
  set damage-demand 0
  set drug-demand 0
  set other-demand 0
  set theft-demand 0
  set weapons-demand 0
  set po-demand 0
  set robb-demand 0
  set shop-demand 0
  set tfp-demand 0
  set veh-demand 0
  set non-crime-demand 0
  set crime-demand 0

end




to print-demand-globals
    print (word "asb-demand = " asb-demand  )
    print (word "bike-demand = " bike-demand  )
    print (word "burg-demand = " burg-demand  )
    print (word "damage-demand = " damage-demand )
    print (word "drug-demand = " drug-demand  )
    print (word "other-demand = " other-demand )
    print (word "theft-demand = " theft-demand )
    print (word "weapons-demand = " weapons-demand )
    print (word "po-demand = " po-demand)
    print (word "robb-demand = " robb-demand )
    print (word "shop-demand = " shop-demand )
    print (word "tfp-demand = " tfp-demand)
    print (word "veh-demand = " veh-demand)
    print (word "viol-sex-demand = " viol-sex-demand   )

end


;main setup procedure
to setup

  ;clear stuff
  ca
  reset-ticks

  ;set enumerations
  set-enumerations


  ;if seeded set the seed from global replication
  if SetSeed [ random-seed replication ]

  ;check that user has specified suitable size CID/ RESPONSE pools for interface - which requires multiples of 10 per shift - if not warn them to reset
  if ((shift-1-response + shift-1-CID) mod 10 != 0) [ user-message "WARNING: Shift 1 allocation must be a multiple of 10 \nPress Halt and reset shift allocation" ]
  if ((shift-2-response + shift-2-CID) mod 10 != 0) [ user-message "WARNING: Shift 2 allocation must be a multiple of 10 \nPress Halt and reset shift allocation" ]
  if ((shift-3-response + shift-3-CID) mod 10 != 0) [ user-message "WARNING: Shift 3 allocation must be a multiple of 10 \nPress Halt and reset shift allocation" ]

  ; init python session
  py:setup py:python
  py:run "from netlogo_adapter import init_model, get_crimes, get_loading, set_loading"

  ; if Force="TEST" canned data rather than the actual model will be used
  ; seed crims MC with replication
  ; burn-in period currently hard-coded to 1 month at 100% loading
  let initial-loading 1.0
  let burn-in-months 1
  py:run (word "init_model(" replication ", '" Force "', " StartYear ", " StartMonth ", " initial-loading ", " burn-in-months ")")

  ;adjust internal ABM date-time to match - and set default timestep to 1 hour
  set timestep-length-minutes 60
  set dt time:create (word StartYear "/" StartMonth "/01 00:00")
  set end-dt (time:plus dt timestep-length-minutes "minutes")

  ; test type - only stalking offences *from the second month* (i.e. after the burn-in)
  ; py:run "set_loading(0.0)"
  ; py:run "set_loading(100.0, 'stalking')"
  ; test category - only burglary category offences *from the second month* (i.e. after the burn-in)
  ; py:run "set_loading(0.0)"
  ; py:run "set_loading(20.0, 'burglary')"

  ;create folder path to store results based on settings
  let model-config (word Force "-" behaviorspace-experiment-name "-" replication "-")
  let path (word "model-output/" behaviorspace-experiment-name "/")
  pathdir:create path

  ;setup output files
  set event-summary-file (word path model-config "event-summary-file.csv")
  set active-event-trends-file (word path model-config "active-event-trends-file.csv")
  set active-resource-trends-file (word path model-config "active-resource-trends-file.csv")
  set resource-summary-file (word path model-config "officer-summary-file.csv")
  set resource-usage-trends-file (word path model-config "resource-usage-trends-file.csv")

  ;size the view window so that 1 patch equals 1 unit of resource - world is 10 resources wide - calculate height and resize
  ;let dim-resource-temp (ceiling (sqrt number-resources)) - 1
  ;calculate the total number of resources by adding up user specified vars
  let number-resources (shift-1-response + shift-2-response + shift-3-response + shift-1-CID + shift-2-CID + shift-3-CID)
  let y-dim-resource-temp (number-resources / 10) - 1
  resize-world 0 9 0 y-dim-resource-temp

  ;initialize shift bools
  set shift-1 false
  set shift-2 false
  set shift-3 false

  ; create police resoruce agents - one per patch -
  ask n-of (number-resources) patches
  [
    sprout-resources 1
    [
      set shape "square"
      set color grey
      set resource-status OFF-DUTY
      set events-completed 0
      ;initially specify all units as response officers
      set resource-type RESPONSE
      set current-event no-turtles

      set max-resource-capacity 1 - non-crime-%-RESPONSE
    ]
  ]

  ;split the agents so that the bottom third work shift 1, middle third shift 2, top third shift 3
  ;take values from the interface that allow users to specify officers in each shift (shift-1-response, shift-2-response, shift-3-response) and
  ;identify where to chop up the visulaisation window and who to allocate to which shift - this complexity is only necessary if we want to visulaize
  ;the shifts grouped together in the UI (otherwise it would just be n-of patches etc)
  let shift-1-split ((shift-1-response + shift-1-CID) / 10)
  let shift-2-split ((shift-2-response + shift-2-CID) / 10)
  let shift-3-split ((shift-3-response + shift-3-CID) / 10)

  ;assign resource agents a working shift - this could be manipulated in future revisions to reflect the fact that officers work a shift rotation
  ask resources with [ycor >= 0 and ycor < (shift-1-split)  ] [ set working-shift 1]
  ask resources with [ycor >= shift-1-split and ycor < (shift-1-split + shift-2-split)] [ set working-shift 2]
  ask resources with [ycor >= (shift-1-split + shift-2-split) and ycor < shift-1-split + shift-2-split + shift-3-split] [ set working-shift 3]

  ; Split police resources into 2 pools - response officers (resource-type = RESPONSE) who deal with lower level incidents and CID who deal with more serious offences
  ; Global vars specify counts of each across shifts shift-1-response, shift-1-CID, shift-2-response, shift-2-CID, shift-3-response, shift-3-CID
  ask n-of (shift-1-CID) resources with [working-shift = 1] [ set shape "star" set resource-type CID set max-resource-capacity 1 - non-crime-%-CID ]
  ask n-of (shift-2-CID) resources with [working-shift = 2] [ set shape "star" set resource-type CID set max-resource-capacity 1 - non-crime-%-CID ]
  ask n-of (shift-3-CID) resources with [working-shift = 3] [ set shape "star" set resource-type CID set max-resource-capacity 1 - non-crime-%-CID ]

  set CID-officers resources with [ resource-type = CID ]
  set RESPONSE-officers resources with [ resource-type = RESPONSE ]

  ; TODO think about burn-in, start logging only once burn-in period finished?
  ;if enabled start logging
  if event-file-out [start-file-out]

  ;midnight so roster shift 3 on
  set shift-3 TRUE
  roster-on 3


  reset-demand-globals

  if not HEADLESS [ output-print "Model Initialised" ]

end



;the main simulation loop
to go-step

  ;print the time
  if not HEADLESS [ output-print (word "\n\n***  " (time:show dt "dd-MM-yyyy HH:mm") " to " (time:show end-dt "dd-MM-yyyy HH:mm") "  *******************************************************************************\n" ) ]

  ;check what the current time is and proceed accordingly to roster shifts on and off
  check-shift
  ;reset the hourly crime count
  set count-crime-timestep 0
  reset-demand-globals
  ;read in current hour's events

  if not HEADLESS [ output-print ("--- TASKING & CO-ORDINATING -----------------------\n") ]

  read-events-from-crims

  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ;TASKING AND CO-ORDINATING with RUDIMENTARY TRIAGE
  ;Three types of response: (1) RESPONSE OFFICERS; (2) CID OFFICERS; (3) NON-PHYSICAL RESPONSE (i.e. resolved over phone or virtually)
  ;Order event priority 1 (RESPONSE & CID), 2 (RESPONSE), 3 (RESPONSE), 4 (with suspect > escalated to priority 3, with no suspect > virtual response)
  ;Within each priority - first ongoing paused incidents > new incidents > understaffed incidents.
  ;event-status - status of demand event - coded 1 = awaiting supply, 2 = ongoing
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ;RESPONSE OFFICER ALLOCATIONS
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  if not HEADLESS [ output-print ("\n--- EVENT OUTCOMES -----------------------\n") ]
  ;PRIORITY 1 -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ask events with [event-priority = 1 and event-resource-type = RESPONSE and event-status = PAUSED] [get-resources-response] ;pickup priority 1 RESPONSE ongoing jobs that are paused first (after they lost all resources at change of shift) - THIS CURRENTLY SHOULDN'T EVER HAPPEN AS INITIAL RESPONSE FOR PRIORITY 1 INCIDENTS IS ONLY EVER 1 HOUR - SO CAN'T SPAN SHIFTS
  ask events with [event-priority = 1 and event-resource-type = RESPONSE and event-status = AWAITING-SUPPLY] [get-resources-response]   ;then new jobs
  ask events with [event-priority = 1 and event-resource-type = RESPONSE and event-status = ONGOING and (count current-resource) < event-resource-req-officers] [replenish-resources-response]   ;then jobs that are ongoing but under staffed - THIS SHOULD ALSO NEVER HAPPEN AS INITIAL RESPONSE IS ONLY EVER 1 HOUR

  ;PRIORITY 2 -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ask events with [event-priority = 2 and event-resource-type = RESPONSE and event-status = PAUSED] [get-resources-response]
  ask events with [event-priority = 2 and event-resource-type = RESPONSE and event-status = AWAITING-SUPPLY] [get-resources-response]
  ask events with [event-priority = 2 and event-resource-type = RESPONSE and event-status = ONGOING and (count current-resource) < event-resource-req-officers] [replenish-resources-response]

  ;PRIORITY 3 -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ask events with [event-priority = 3 and event-resource-type = RESPONSE and event-status = PAUSED] [get-resources-response]
  ask events with [event-priority = 3 and event-resource-type = RESPONSE and event-status = AWAITING-SUPPLY] [get-resources-response]
  ask events with [event-priority = 3 and event-resource-type = RESPONSE and event-status = ONGOING and (count current-resource) < event-resource-req-officers] [replenish-resources-response]
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ;CID ALLOCATION
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ask events with [event-resource-type = CID and event-status = PAUSED] [rejoin-job-CID]   ;Try to reallocate CID staff to their allotted cases when they roster back on - this catches jobs that have been paused as everyone rostered off
  ask events with [event-resource-type = CID and event-status = ONGOING and (count current-resource with [resource-status = ON-DUTY-RESPONDING]) < event-resource-req-officers] [rejoin-job-CID] ;then jobs that are ongoing but under staffed - count of current-resource has to look who is active as off duty officers are still included (allowing CID officers to keep track of current cases)
  ask events with [event-resource-type = CID and event-status = AWAITING-SUPPLY] [get-resources-CID-parallel]   ;finally CID jobs that are currently unallocated - this order prevents officers as already assigned to particular jobs being assigned to new jobs prior to returning to their existing jobs
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ;NO RESPONSE - PRIORITY 4
  ;------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  ask events with [event-priority = 4 and event-status = AWAITING-SUPPLY ] [ resolve-without-response ]   ;first resolve priority 4 incidents without physical resposne

  ;update visualisations - do this after resources have been allocated and before jobs have finished - so that plots reflect actual resource usage 'mid-hour' as it were
  ask resources [  draw-resource-status ]


  ;check status of ongoing events so those about to complete can be closed
  ask events with [event-status = ONGOING and event-resource-type = RESPONSE] [ check-event-status ] ; RESPONSE EVENTS
  ask events with [event-status = ONGOING and event-resource-type = CID] [ check-event-status ] ; CID EVENTS

  update-all-plots

  ;tick by one hour

  ;print-demand-globals
  increment-time

end







;Procedure to check datetime and adjust flags for shifts currently active/inactive, and roster officers on or off
to check-shift

  ;3 Overlapping Shifts:
  ;1. 0700 - 1700
  ;2. 1400 - 2400
  ;3. 2200 - 0700

  let hour time:get "hour" dt

  ;Shift 1
  if hour = 7 [ set shift-1 TRUE set Shift-3 FALSE roster-on 1 roster-off 3]
  if hour = 17 [ set shift-1 FALSE  roster-off 1 ]

  ;Shift 2
  if hour = 14 [ set shift-2 TRUE roster-on 2 ]
  if hour = 0 [ set shift-2 FALSE roster-off 2]

  ;Shift 3
  if hour = 22 [ set shift-3 TRUE roster-on 3]

end

; python interface
; get the current time
; to-report pytime
;   let call "get_time()"
;   report py:runresult call
; end

; get the current time
; to-report pydone
;   let call "at_end()"
;   report py:runresult call
; end

; get data from upstream model
to-report pycrimes [start]
  ; serialise start/end into strings as can't pass a netlogo time type
  let ts time:show start "yyyy-MM-dd HH:mm:ss"
  let te time:show (time:plus start 1 "hours") "yyyy-MM-dd HH:mm:ss"
  let call (word "get_crimes('" ts "', '" te  "')")
  report py:runresult call
end




;increment internal tick clock and date time object - 1 tick = 1 hour
to increment-time
  tick
  set dt end-dt
  set end-dt (time:plus dt timestep-length-minutes "minutes")
end







; procedure to read in the events for the given time window / tick
to read-events-from-crims

  ;API DATA FORMAT
  ;0    1           2               3       4                                             5                     6           7
  ;id   MSOA        crime_category  code    description                                   time                  suspect     severity
  ;0    E02004312   vehicle crime   45      Theft from vehicle                            2020-07-01 00:01:00   false       32.92067737
  ;12   E02004313   vehicle crime   48      Theft or unauthorised taking of motor vehicle 2020-07-01 00:16:00   true        128.4294318

  let event-data csv:from-string pycrimes dt
  ; remove header row
  set event-data remove-item 0 event-data

  set count-crime-timestep count-crime-timestep + length event-data ; increment crime count
  while [length event-data > 0]
  [
    ; grab the first crime
    let temp item 0 event-data
    ;create an event agent
    create-events 1
    [
      set hidden? true       ;make it invisible
      set event-resource-type RESPONSE  ;all events initially response

      ;fill in relevant details for event from crims data
      set eventID item 0 temp
      set event-type item 4 temp
      set event-class item 2 temp
      set event-MSOA item 1 temp
      set event-severity item 7 temp
      set event-suspect item 6 temp
      set event-start-dt dt
      set event-status AWAITING-SUPPLY ;awaiting resource

      ;get event priority based on severity
      convert-severity-to-event-priority


      ;lookup if you need jut RESPONSE or RESPONSE & CID based on expert insight
      set event-requires-CID? get-CID-requirements Expert-CID-Allocation event-type

      ;get requirements in terms of RESPONSE & CID hours/officers
      generate-event-requirements



    ]
    ;once the event agent has been created delete it from the data file
    set event-data remove-item 0 event-data

  ]

end




; New method to identify requirements for Response and CID resources to events based on prioriy, severity, the presence of a suspect and the current shift (to accomodate safe crewing)
to generate-event-requirements



  ; TODO can 1/2/3 be dealt with in a single if block (+ if 1, call CID)
  ;PRIORITY 1 Events - RESPONSE & CID officers
  ;For priority 1 events we model an initial hour of RESPONSE OFFICER time (single or double crewed depending on shift and options) and then create a new knock on event for CID to deal with using call-CID
  if event-priority = 1
  [
    ;get one hour of response officer(s) time for immediate response to priority 1 events then handover to CID to complete job
    set event-resource-req-hours 1
    ifelse Shift-3 ;Night (shift 3) or Day (shifts 1,2) - check double crewing options
    [ifelse response-safe-crewing-NIGHT [set event-resource-req-officers 2] [set event-resource-req-officers 1]]
    [ifelse response-safe-crewing-DAY [set event-resource-req-officers 2] [set event-resource-req-officers 1]]
    set event-resource-req-total (event-resource-req-hours * event-resource-req-officers)
    set event-resource-counter event-resource-req-total
    if not HEADLESS [ output-print (word EventID " INITIAL-RESPONSE-ALLOCATION "  ",resource_type=" event-resource-type " , offence=" event-type ", Priority="  event-priority ", Severity="event-severity ", suspect=" event-suspect ", Response Hours=" event-resource-req-hours ", Response Officers=" event-resource-req-officers ) ]

    ;if the event requires a CID response - then call CID and create a follow up event
    if event-requires-CID? [ call-CID ]
  ]

  ;PRIORITY 2 & 3 Events - RESPONSE officers only
  ;For priority 2 & 3 events we calculate RESPONSE OFFICER time only (single or double crewed depending on shift and options)
  if (event-priority = 2 or event-priority = 3)
  [
    ;calculate hours required based on severity and presence/absence of suspect (final parameter an optional weight to over/under concentrate on case - increase/decrease hours = hardcoded to 1 no effect)
    set event-resource-req-hours convert-severity-to-resource-time event-severity event-suspect 1 RESPONSE-RESOURCE-LINEAR
    ifelse Shift-3 ;Night (shift 3) or Day (shifts 1,2) - check double crewing options
    [ifelse response-safe-crewing-NIGHT [set event-resource-req-officers 2] [set event-resource-req-officers 1]]
    [ifelse response-safe-crewing-DAY [set event-resource-req-officers 2] [set event-resource-req-officers 1]]
    ;calculate total person hours
    set event-resource-req-total  (event-resource-req-hours * event-resource-req-officers)
    set event-resource-counter event-resource-req-total
    if not HEADLESS [ output-print (word EventID " RESPONSE-ALLOCATION "  ",resource_type=" event-resource-type " , offence=" event-type ", Priority="  event-priority ", Severity="event-severity ", suspect=" event-suspect ", Response Hours=" event-resource-req-hours ", Response Officers=" event-resource-req-officers ) ]

    ;if the event requires a CID response - then call CID and create a follow up event
    if event-requires-CID? [ call-CID ]

  ]

  ;PRIORITY 4 Events - NO PHYSICAL RESPONSE
  ;For priority 4 events - virtual or no physical response
  if (event-priority = 4)
  [
    ;get hour of a single response officer
    set event-resource-req-hours 0
    set event-resource-req-officers 0
    set event-resource-req-total  0
    set event-resource-counter 0
    if not HEADLESS [ output-print (word EventID " VIRTUAL-RESPONSE " ",resource_type=" event-resource-type " , offence=" event-type ", Priority="  event-priority ", Severity="event-severity ", suspect=" event-suspect ", Response Hours=" event-resource-req-hours ", Response Officers=" event-resource-req-officers ) ]
  ]
end


;Method called by priority 1 response events to create a knock on CID event
to call-CID
  hatch 1 ;inherets all properties of response event - i.e. crime type, location etc.
  [
    ;give it a unique ID
    set eventID (word eventID "-CID")
    set event-resource-type CID
    ;one CID officer - no double crewing for CID
    set event-resource-req-officers 1
    ;calculate hours required based on severity and presence/absence of suspect (final parameter an optional weight to over/under concentrate on case - increase/decrease hours = hardcoded to 1 no effect)
    set event-resource-req-hours convert-severity-to-resource-time event-severity event-suspect 1 CID-RESOURCE-LINEAR
    set event-resource-req-total  (event-resource-req-hours * event-resource-req-officers)
    set event-resource-counter event-resource-req-total

    if not HEADLESS [ output-print (word EventID " FOLLOWUP-CID-ALLOCATION "  ",resource_type=" event-resource-type " , offence=" event-type ", Priority="  event-priority ", Severity="event-severity ", suspect=" event-suspect ", CID Hours=" event-resource-req-hours ", CID Officers=" event-resource-req-officers ) ]
  ]
end





; Function that calculates number of hours a case will need based on severity of offence, presence or absence of a suspect, a weight which allows manipulation of
; how much resource is allocated to particular offences (NOT USED), and a GUI Flag (linear) which specifies which formula should be used for calculating the severity > hours relationship
to-report convert-severity-to-resource-time [ severity suspect weight linear ]
  ;double severity if there's a suspect and divide by 100
  let s 1
  if suspect [set s 2]
  let mean-log-time 0

  ifelse linear
  [
    ;LINEAR
    ; sample lognormal
    set mean-log-time ln(severity * s / 200)
  ]

  [
    ;NON-LINEAR
    ;calibrated a quadratic growth in time asscociated with offences - here we calibrate such that the linear method above and the exponential method meet at severity = 1000 (the threshold for priority 4 incidents)
    set mean-log-time 2 * ln((severity) * s / 440)
  ]

  ; A fixed s.d. in log space translates to a proporational one in actual (time) space, e.g. for mean=10, 1 s.d.=(8.33-12) and for mean=100, 1 s.d.=(83.3-120)
  let stdev-log-time 0.2 ;* sqrt(ln(severity))

  ; sample time and round up to nearest whole hour
  let time ceiling exp(random-normal mean-log-time stdev-log-time)

  ; show (word severity " ONS CSS - mean=" exp(mean-time) " -- time=" time)
  report time
end













; return priority 1,2,3,4 based on severity (and presenece of suspect) - should implement THRIVE here
; Events 1000 or more severity - PRIORITY 1 - CID Response
; Events 500 <> 999 - PRIORITY 2 - Response Officer Response
; Events 499 <> 100 = PRIORITY 3 - Response Officer Response
; Events < 100 with a SUSPECT = PRIORITY 3  - Response Officer Response
; Events < 100 with NO SUSPECT = PRIORITY 4 - Resolved without response
to convert-severity-to-event-priority
  (ifelse
    event-severity >= 1000 [ set event-priority 1 ]
    event-severity >= 500 [ set event-priority 2 ]
    event-severity >= 100 [set event-priority 3 ]
    [ ifelse event-suspect [ set event-priority 3 ] [ set event-priority 4 ]] ;less than 100 see if suspect present if yes, escalate
  )

  ; show (word event-severity " ONS CSS - priority=" event-priority)
  ; show (word event-type " severity:" event-severity " suspect:" event-suspect " = PRIORITY " event-priority)
end


to roster-on [ shift ]
  ;as a shift changes roster on new staff - shift sizes now specified by user - note overlap between shifts
  ask resources with [resource-status = OFF-DUTY and working-shift = shift] [set resource-status ON-DUTY-AVAILABLE ]

end




;procedure that takes all officers currently working off shift and places all ongoing jobs back onto the pile of current jobs to be picked up by the next officers
;could implement overtime here such that officers worked longer, or finished their current job.
to roster-off [ shift ]

  ;ROSTER OFF RESPONSE COPS - THEY FORGET EVERYTHING
  ask RESPONSE-officers with [ working-shift = shift]
  [
    set resource-status OFF-DUTY
    set current-event no-turtles
  ]

  shift-drop-events-RESPONSE shift

  ;ROSTER OFF CID COPS - THEY REMEMBER CURRENT CASE AND RETURN TO IT
  ask CID-officers with [working-shift = shift]
  [
    set resource-status OFF-DUTY
  ]

  shift-drop-events-CID shift

end



;These two methods clean up events that will be affected by the availability of officers given a shift change.
; RESPONSE officer jobs are simply transfered from officers in the closing shift to new officers in the starting shift - thus ensuring continuity of service
; - note there is a special case whereby multiple officers have been assigned to a job from multiple shifts and this leaves a job ongoing but understaffed at shift change - this is picked up in tasking and coordinating
; CID officers are allotted to a cases that occur during their active shift, when they leave work if an event has no active resource left it is paused until they return to work to pick it up
; - this allows us to model the fact that CID officers will wrk a case until the end rather than just hand it between officers

to shift-drop-events-RESPONSE  [ shift ]
  ;look at all ongoing events
  ask events with [ event-status = ONGOING and event-resource-type = RESPONSE]
  [
    ; remove any officers that are about to roster off from the current resource
    set current-resource current-resource with [working-shift != shift]
    ;check if that leaves any resource left
    if count current-resource = 0
    [
      ;if not pause the event and set its status back to 1
      set event-status PAUSED
      if VERBOSE [output-print (word eventID " - PAUSED due to lack of staff - further " event-resource-counter " person hours required to complete this event")]
    ]
  ]
end

to shift-drop-events-CID  [ shift ]

  let next-shift shift + 1
  if next-shift = 4 [set next-shift 1]

  ;look at all omngoing events
  ask events with [ event-status = ONGOING and event-resource-type = CID]
  [
    ;count how many staff will be left working on this event after specified shift ends
    let available-resource count current-resource with [working-shift = next-shift]
    ;output-print (word "available-resource count = " available-resource)
    ; if it's 0 pause the event and wait for assigned officer to return to work (note that above - we dissociate the event with the response officer as it will be picked up by another officer in the next shift, here we want CID officers to work on the same cases from start to finish when they are in work
    if available-resource = 0
    [
      set event-status PAUSED
      if VERBOSE [output-print (word eventID " - CID PAUSED - waiting for " [self] of current-resource " to return to work - " event-resource-counter " additional person hours required to complete this event")]
    ]
  ]
end


; Main method to decrement requirements of ongoing events and close off events as they are completed
to check-event-status

  ; Count up the work spent on current event this timstep - then remove it from the event-resource-counter
  ; 1 / workload allows CID agents with multiple cases to contribute sum proportion of person/hour per hour to a particular event - this assumes a CID with multiple cases devotes equal time to each.
  ; for CID officers workload can be > 1, for RESPONSE workload = 1 (thus, they devote all their time tocurrent event
  ; total is the sum contribution accross all officers currently allocated to the event - the 1 in this equation could be parameterised to reflect that officers only have some proporition of time each hour for crime-related activity - i.e. at 0.5 time able to be spent on crime halves.

  let work-done 0
  if event-resource-type = CID
  [
    set work-done sum [(1 - non-crime-%-CID) / (count current-event)] of current-resource with [resource-status = ON-DUTY-RESPONDING]
    ;add to global counter of non-crime-demand this hour
    set non-crime-demand non-crime-demand + (1 - non-crime-%-CID)
  ]
  if event-resource-type = RESPONSE
  [
    set work-done sum [(1 - non-crime-%-RESPONSE) / (count current-event)] of current-resource with [resource-status = ON-DUTY-RESPONDING]
    ;add to global counter of non-crime-demand this hour
    set non-crime-demand non-crime-demand + (1 - non-crime-%-RESPONSE)
  ]

  if VERBOSE [output-type (word eventID " ") ask current-resource [ output-type (word self " contributing " (1 / (count current-event)) " p/h ") ]]
  ; now decrement this amount from the event-resource-counter
  set event-resource-counter (event-resource-counter - work-done)


  ;log demand - this is not very efficient - ordering the case statement by frequency of offences will presumably help a little - but still
  (ifelse
    event-class = "violence and sexual offences" [ set viol-sex-demand  viol-sex-demand + work-done ]
    event-class = "anti-social behaviour" [ set asb-demand  asb-demand  + work-done ]
    event-class = "bicycle theft" [ set bike-demand  bike-demand  + work-done ]
    event-class = "burglary" [ set burg-demand  burg-demand  + work-done ]
    event-class = "criminal damage and arson" [ set damage-demand  damage-demand + work-done ]
    event-class = "drugs" [ set drug-demand  drug-demand + work-done ]
    event-class = "other crime" [ set other-demand other-demand + work-done ]
    event-class = "other theft" [ set theft-demand theft-demand + work-done ]
    event-class = "possession of weapons" [ set weapons-demand  weapons-demand + work-done ]
    event-class = "public order" [ set po-demand po-demand + work-done ]
    event-class = "robbery" [ set robb-demand robb-demand + work-done ]
    event-class = "shoplifting" [ set shop-demand shop-demand + work-done ]
    event-class = "theft from the person" [ set tfp-demand tfp-demand + work-done ]
    event-class = "vehicle crime" [ set veh-demand veh-demand + work-done ]
  )






  if VERBOSE [output-print (word "Job ongoing - requires = " event-resource-req-total " --- currently " count current-resource " officers allocated - total p/h=" work-done " now " event-resource-counter " resource hours remaining")]

  ;Now check if the event can be resolved this cycle?
  if event-resource-counter <= 0
  [
    ; if so - end the event, record that, relinquish resource(s), destroy the event agent
    ask current-resource [ relinquish ]
    set count-completed-events count-completed-events + 1
    if not HEADLESS [ output-print (word EventID " - EVENT COMPLETE - " event-type " - Priority=" event-priority ", Event-Arrival=" (time:show event-start-dt "dd-MM-yyyy HH:mm") ", Response-Start=" (time:show event-response-start-dt "dd-MM-yyyy HH:mm") ", Response-Complete=" (time:show end-dt "dd-MM-yyyy HH:mm") ", Timetaken=" (time:difference-between event-response-start-dt end-dt "hours") " hours") ]
    if event-file-out [write-completed-event-out]
    die
  ]

end


; event procedure that completes priority 4 events via virtual or without physical response (threshold for priority 4 events defined in convert-severity-to-priority)
to resolve-without-response

  set count-completed-events count-completed-events + 1
  if not HEADLESS [ output-print (word EventID " - EVENT COMPLETE (without physical response) - " event-type " - Priority=" event-priority ", Event-Arrival=" (time:show dt "dd-MM-yyyy HH:mm") ", Response-Start=" (time:show dt "dd-MM-yyyy HH:mm") ", Response-Complete=" (time:show dt "dd-MM-yyyy HH:mm") ", Timetaken=" (time:difference-between dt dt "hours") " hours") ]
  if event-file-out [write-completed-without-response]
  die

end


to relinquish
  ;reduce workload by 1

  ;count a completed event for that individual officer
  set events-completed events-completed + 1

  ;if destroying this event agent will leave your count-events at 0 (the event will die after relinquish has run)
  if (count current-event) - 1 = 0 [ if resource-status = ON-DUTY-RESPONDING [set resource-status ON-DUTY-AVAILABLE]] ;if relinquishing this job sets your workload to 0 and you are currently rostered on make yourself availble
                                                                    ;- the check on resource status is for the edge case whereby a job is split between officers at multiple shifts
                                                                   ;and one officer completes the job while the other is rostered off, in this case we should leave resource-status at OFF-DUTY
end



;RESOURCE ALLOCATION METHODS ------------------------------------------------------------------------------------------------------------------------------------

; event procedure to assess if sufficient resources are available to respond to event and if so allocate them to it
to get-resources-CID-parallel
  ;check if the required number of CID resources are available that are COMPLETELY FREE
  ifelse count CID-officers with [resource-status = ON-DUTY-AVAILABLE] >= (event-resource-req-officers)
  [
    if VERBOSE [output-print (word EventID " - CID OFFICERS responding to priority " event-priority " " event-type " event - " event-resource-req-officers " unit(s) required for " event-resource-req-hours " hour(s) - TOTAL RESOURCE REQ = " event-resource-req-total " REMAINING = " event-resource-counter )]
    ;link resource to event
    set current-resource n-of event-resource-req-officers CID-officers with [resource-status = ON-DUTY-AVAILABLE]

    ;if this is a new event (not one that is paused) record start datetime of response
    if event-status = AWAITING-SUPPLY [set event-response-start-dt dt]
    set event-status ONGOING ; mark the event as allocated and ongoing

    ask current-resource
    [
      set current-event (turtle-set current-event myself)
      set resource-status ON-DUTY-RESPONDING
    ]
  ]

  ;in this scenario there are not enough complelety free CID resources - but an event must be responded to so start to split jobs
  [
    if VERBOSE [output-print (word EventID " - active CID OFFICERS being partially allocated to priority " event-priority " " event-type " event - " event-resource-req-officers " unit(s) required for " event-resource-req-hours " hour(s) - TOTAL RESOURCE REQ = " event-resource-req-total " REMAINING = " event-resource-counter )]

    ;user-message "Not enough CID officers - job split needed"
    ;find the currently on shift but responding officers with the lowest current workload and assign them to the job
    set current-resource min-n-of event-resource-req-officers CID-officers with [resource-status = ON-DUTY-AVAILABLE or resource-status = ON-DUTY-RESPONDING] [(count current-event)]

    ;if this is a new event (not one that is paused) record start datetime of response
    if event-status = AWAITING-SUPPLY [set event-response-start-dt dt]
    set event-status ONGOING ; mark the event as allocated ongoing

    ask current-resource
    [
      ; add the new job to the current event turtle set
      set current-event (turtle-set current-event myself)
      ;set current-event-type [event-type] of current-event
      ;set current-event-class [event-class] of current-event
      ;set workload workload + 1 ;increase  workload
    ]


  ]
end



;method to check for CID Officers assigned to a job but currently offshift and reallocate them to their current job when they roster back on
to rejoin-job-CID
  if VERBOSE [
    output-type (word EventID " waiting for ")
    ask current-resource with [resource-status != 2] [output-type (word self ",")]
    output-print ""
  ]
  ; for CID Jobs current-resource contains a list of all agents who are assigned to the job - this can include officers who are currently rostered off
  ; - when they are rostered back on this catches them and reallocated them to their ongoing job
  ask current-resource
  [
    ;if one or more of my current-resource has just been rostered on - reallocate them
    if resource-status = ON-DUTY-AVAILABLE
    [
      ;output-print (word self " returning to " [EventID] of current-event)
      ask current-event [ set event-status ONGOING ] ;if all staff have been rostered off the event will be paused - when you add 1 or more officers unpause it and set is as ongoing
      set resource-status ON-DUTY-RESPONDING
    ]
  ]
end



; event procedure to assess if sufficient RESPONSE resources are available to respond to event and if so allocate them to it
to get-resources-response
  ;check if the required number of CID resources are currently available if not event remains unallocated
  if count RESPONSE-officers with [resource-status = ON-DUTY-AVAILABLE] >= (event-resource-req-officers)
  [
    if VERBOSE [output-print (word EventID " - RESPONSE OFFICERS responding to priority " event-priority " " event-type " event - " event-resource-req-officers " unit(s) required for " event-resource-req-hours " hour(s) - TOTAL RESOURCE REQ = " event-resource-req-total  " REMAINING = " event-resource-counter )]
    ;link responce resource to event
    set current-resource n-of event-resource-req-officers RESPONSE-officers with [resource-status = ON-DUTY-AVAILABLE]

    ;if this is a new event (not one that is paused) record start datetime of response
    if event-status = AWAITING-SUPPLY [set event-response-start-dt dt]
    ;set event-response-end-dt time:plus dt (event-resource-req-time) "hours"
    set event-status ONGOING ; mark the event as ongoing

    ask current-resource
    [
      ;link back to the event
      set current-event (turtle-set current-event myself)
      ;set as working on job
      set resource-status ON-DUTY-RESPONDING
    ]
  ]
end



; event procedure to assess if sufficient resources are available to replenish an ongoing but understaffed current event and if so allocate them to it
; understaffed but still active events can be created when a job is allocated to multiple officers who span consecutive shifts (this can happen if the eventoccurs when two shifts are active)
; - at shift change some officers may be rostered off leaving some number of still rostered on officers still working - these functions identify these jobs and replenish them with other officers from the next shift
; note that typically jobs are allocated officers from the same shift, thus at shift change they are paused and then reallocated resources from the new shift using get-resources above
; these functions just catch the special case described above.


; event procedure to assess if sufficient RESPONSE resources are available to replenish an ongoing but understaffed current event (due to shift change)  and if so allocate them to it
to replenish-resources-response
  ;check if the required number of resources are available to replenish job
  if count RESPONSE-officers with [resource-status = ON-DUTY-AVAILABLE ] >= (event-resource-req-officers - (count current-resource))
  [
    if VERBOSE [output-print (word EventID " - Adding RESPONSE officers to " event-type " event - " event-resource-req-officers " unit(s) required for " event-resource-req-hours " hour(s) - TOTAL RESOURCE REQ = " event-resource-req-total)]

    ;link new resources to event with the old resources
    set current-resource (turtle-set (current-resource) n-of (event-resource-req-officers - (count current-resource)) RESPONSE-officers with [resource-status = ON-DUTY-AVAILABLE])

    ;relink new resource group back to event
    ask current-resource
    [
      ;link event to resource
      set current-event (turtle-set current-event myself)
      set resource-status ON-DUTY-RESPONDING
    ]
  ]
end


;-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

;VISUALISATION METHODS -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

; color resource agents based on current state - blue for responding - grey for available
to draw-resource-status

  if resource-status = OFF-DUTY [ set color grey ] ; rostered off
  if resource-status = ON-DUTY-AVAILABLE [ set color white ] ; active & available
  if resource-status = ON-DUTY-RESPONDING [ set color blue ] ; active & on event
  ifelse show-workload [set plabel (count current-event)] [set plabel ""]

end



;plot update commands
to update-all-plots

  ;"date_time,CIDusagePCT,RESPONSEusagePCT,priority1_ongoing,priority2_ongoing,priority3_ongoing,piority1_waiting,piority2_waiting,piority3_waiting,RESPONSE_ongoing,CID _ongoing,meanCIDworkload_current_shift, meanCIDworkload_all"

  file-open resource-usage-trends-file
  file-print (word (time:show dt "dd-MM-yyyy HH:mm") ","
    shift-1 ","
    shift-2 ","
    shift-3 ","
    ((count CID-officers with [resource-status = ON-DUTY-RESPONDING] / count CID-officers with [resource-status = ON-DUTY-RESPONDING or resource-status = ON-DUTY-AVAILABLE] ) * 100) ","            ;% Usage CID
    ((count RESPONSE-officers with [resource-status = ON-DUTY-RESPONDING] / count RESPONSE-officers with [resource-status = ON-DUTY-RESPONDING or resource-status = ON-DUTY-AVAILABLE] ) * 100) ","  ;% Usage RESPONSE
    (count events with [event-status = ONGOING and event-priority = 1]) ","                    ; Count Ongoing Priority 1 Jobs
    (count events with [event-status = ONGOING and event-priority = 2]) ","                    ; Count Ongoing Priority 2 Jobs
    (count events with [event-status = ONGOING and event-priority = 3]) ","                    ; Count Ongoing Priority 3 Jobs
    (count events with [event-status = AWAITING-SUPPLY and event-priority = 1]) ","            ; Count Waiting Priority 1 Jobs
    (count events with [event-status = AWAITING-SUPPLY and event-priority = 2]) ","            ; Count Waiting Priority 2 Jobs
    (count events with [event-status = AWAITING-SUPPLY and event-priority = 3]) ","            ; Count Waiting Priority 3 Jobs
    (count events with [(event-status = ONGOING or event-status = PAUSED) and event-resource-type = RESPONSE]) ","        ; Count ongoing RESPONSE jobs
    (count events with [(event-status = ONGOING or event-status = PAUSED) and event-resource-type = CID]) ","             ; Count ongoing CID jobs
    mean [(count current-event)] of resources with [(resource-status = ON-DUTY-AVAILABLE or resource-status = ON-DUTY-RESPONDING) and resource-type = CID] "," ;mean CID officer workload on current shift
    mean [(count current-event)] of resources with [resource-type = CID] ;mean CID officer workload - all CID
  )

  set-current-plot "Crime"
  set-current-plot-pen "total"
  plot count-crime-timestep

  set-current-plot "% Resource Usage"

  if count CID-officers with [resource-status = ON-DUTY-AVAILABLE] > 0
  [
    set-current-plot-pen "CID"
    plot (count CID-officers with [resource-status = ON-DUTY-RESPONDING] / count CID-officers with [resource-status = ON-DUTY-RESPONDING or resource-status = ON-DUTY-AVAILABLE] ) * 100
  ]
  set-current-plot-pen "RESPONSE"
  plot (count RESPONSE-officers with [resource-status = ON-DUTY-RESPONDING] / count RESPONSE-officers with [resource-status = ON-DUTY-RESPONDING or resource-status = ON-DUTY-AVAILABLE] ) * 100

  set-current-plot "Events Waiting"
  set-current-plot-pen "waiting-1"
  plot count events with [event-status = AWAITING-SUPPLY and event-priority = 1]
  set-current-plot-pen "waiting-2"
  plot count events with [event-status = AWAITING-SUPPLY and event-priority = 2]
  set-current-plot-pen "waiting-3"
  plot count events with [event-status = AWAITING-SUPPLY and event-priority = 3]


  set-current-plot "Events Ongoing"
  set-current-plot-pen "CID-Ongoing"
  plot count events with [(event-status = ONGOING or event-status = PAUSED) and event-resource-type = CID]
  set-current-plot-pen "RESPONSE-Ongoing"
  plot count events with [(event-status = ONGOING or event-status = PAUSED) and event-resource-type = RESPONSE]


  ;------------------------------------------------------------------------------------------------------------------------------

  ;plotting and recording the amount of events currently being responded to by crime-classes this hour
  set-current-plot "active-events"
  file-open active-event-trends-file
  ;only look at active events
  let current-events events with [event-status = ONGOING]
  let out-string (word (time:show dt "dd-MM-yyyy HH:mm") ",")

  set-current-plot-pen "Anti-social behaviour"
  let x count current-events with [event-class = "anti-social behaviour"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Bicycle theft"
  set x count current-events with [event-class = "bicycle theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Burglary"
  set x count current-events with [event-class = "burglary"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Criminal damage and arson"
  set x count current-events with [event-class = "criminal damage and arson"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Drugs"
  set x count current-events with [event-class = "drugs"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other crime"
  set x count current-events with [event-class = "other crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other theft"
  set x count current-events with [event-class = "other theft"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Possession of weapons"
  set x count current-events with [event-class = "possession of weapons"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Public order"
  set x count current-events with [event-class = "public order"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Robbery"
  set x count current-events with [event-class = "robbery"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Shoplifting"
  set x count current-events with [event-class = "shoplifting"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Theft from the person"
  set x count current-events with [event-class = "theft from the person"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Vehicle crime"
  set x count current-events with [event-class = "vehicle crime"]
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Violence and sexual offences"
  set x count current-events with [event-class = "violence and sexual offences"]
  plot x
  set out-string (word out-string x)

  file-print out-string


  ;------------------------------------------------------------------------------------------------------------------------------

  ;plotting and recording the amount of resources devoted to crime-classes this hour
  set-current-plot "resources"
  file-open active-resource-trends-file
  set out-string (word (time:show dt "dd-MM-yyyy HH:mm") ",")

  set-current-plot-pen "Anti-social behaviour"
  set x asb-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Bicycle theft"
  set x bike-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Burglary"
  set x burg-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Criminal damage and arson"
  set x damage-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Drugs"
  set x drug-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other crime"
  set x other-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Other theft"
  set x theft-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Possession of weapons"
  set x weapons-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Public order"
  set x po-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Robbery"
  set x robb-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Shoplifting"
  set x shop-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Theft from the person"
  set x tfp-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Vehicle crime"
  set x veh-demand
  plot x
  set out-string (word out-string x ",")

  set-current-plot-pen "Violence and sexual offences"
  set x viol-sex-demand
  plot x
  set out-string (word out-string x)

  file-print out-string

end


;FILE HANDLING ------------------------------------------------------------------------------------------------------------------------------------------------------------

to start-file-out

  file-close-all

  if file-exists? event-summary-file [file-delete event-summary-file]
  file-open event-summary-file
  file-print "eventID,priority,response_type,type,class,LSOA,start_dt,response_start_dt,response_end_dt,total_hours,response_start_to_end_hours,wait_prior_to_start_hours,count_resources,hours_required,count_officers,total_requirement"

  if file-exists? active-event-trends-file [file-delete active-event-trends-file]
  file-open active-event-trends-file
  file-print "date_time,Anti_social_behaviour,Bicycle_theft,Burglary,Criminal_damage_and_arson,Drugs,Other_crime,Other_theft,Possession_of_weapons,Public_order,Robbery,Shoplifting,Theft_from_the_person,Vehicle_crime,Violence_and_sexual_offences"
  if file-exists? active-resource-trends-file [file-delete active-resource-trends-file]
  file-open active-resource-trends-file
  file-print "date_time,Anti_social_behaviour,Bicycle_theft,Burglary,Criminal_damage_and_arson,Drugs,Other_crime,Other_theft,Possession_of_weapons,Public_order,Robbery,Shoplifting,Theft_from_the_person,Vehicle_crime,Violence_and_sexual_offences"

  if file-exists? resource-usage-trends-file [file-delete resource-usage-trends-file]
  file-open resource-usage-trends-file
  file-print "date_time,shift1,shift2,shift3,CIDusagePCT,RESPONSEusagePCT,priority1_ongoing,priority2_ongoing,priority3_ongoing,piority1_waiting,piority2_waiting,piority3_waiting,response_ongoing,CID_ongoing,meanCIDworkload_shift, meanCIDworkload_all"


end

to close-files

  ;its the end of teh simulation so write out histories of agents
  if file-exists? resource-summary-file [file-delete resource-summary-file]
  file-open resource-summary-file
  file-print "resourceID, resource_type, shift, max_capacity, events_completed"
  ask resources [ file-print (word who "," resource-type "," working-shift "," max-resource-capacity "," events-completed) ]

  ;then close all the files
  file-close-all
end


;write out info on a completed event
to write-completed-event-out

  ;"eventID,priority,response-type,type,class,MSOA,start-dt,response-start-dt,response-end-dt,total-hours,response-start-to-end-hours,wait-prior-to-start-hours,count-resources,hours-required,count-officers,total-requirement"

  file-open event-summary-file
  let out-string (word
    eventID ","   													                       	 									 			;eventID,													
    event-priority "," 				  								                   	 									 			;priority,	
    "Physical,\""														                       	 									 			;response-type,
    (remove "," event-type) "\",\""  											         	 									 			;event-type,
    (remove "," event-class) "\","  												       	 									 			;event-class,
    event-MSOA ","  												                       	 									 			;event-MSOA,

    (time:show event-start-dt "dd-MM-yyyy HH:mm") ","  				     	 									 			;event-start-dt,
    (time:show event-response-start-dt "dd-MM-yyyy HH:mm")  "," 	 	 									 			;event-response-start-dt,
    (time:show end-dt "dd-MM-yyyy HH:mm") ","  						         	 									 			;event-response-end-dt,

    (time:difference-between (event-start-dt) (dt) "hours") "," 				                    ;total-hours,
    (time:difference-between (event-response-start-dt) (dt) "hours")	"," 	                ;response-start-to-end-hours
    (time:difference-between (event-start-dt) (event-response-start-dt) "hours")	"," 			;wait-prior-to-start-hours


    count current-resource ","			 									 									 									 	;count-resources,							
    event-resource-req-hours ","  										 									 									 	;hours-required,
    event-resource-req-officers ","  									 									 									 	;count-officers,
    event-resource-req-total  											 									 									 	  ;total-requirement
    																	
  )  				



  file-print out-string 												

end



;write out info on an event completed without response
to write-completed-without-response
  file-open event-summary-file
  file-print (word
    eventID ","   																																				  ;eventID,													
    event-priority "," 				  																													  ;priority,	
    "Virtual,\""																																					  ;response-type,
    (remove "," event-type) "\",\"" 																											  ;event-type,
    (remove "," event-class) "\","  																												;event-class,
    event-MSOA ","  																																			  ;event-LSOA,

    (time:show dt "dd-MM-yyyy HH:mm") "," 																								  ;total-hours,
    (time:show dt "dd-MM-yyyy HH:mm") ","																										;response-start-to-end-hours
    (time:show dt "dd-MM-yyyy HH:mm") ","																				            ;wait-prior-to-start-hours

    		"0,"																																								;total-hours,
    		"0,"																																								;response-start-to-end-hours
    		"0,"																																								;wait-prior-to-start-hours

    		"0,"        																																				;count-resources,		
    		"0," 																																								;hours-required,
    		"0," 																																								;count-officers,
    		"0" 																																								;total-requirement
  )

end






; function to return bool if offence needs a CID response
; two ways of doing this (specified via expert-insight? parameter)
; if expert-insight? is true we use a lookup table specified by talking to experts
; if not we defer to all offences with a severity of 1000 or more

to-report get-CID-requirements [ expert-insight? offence ]

  let requires-CID? 0

  ifelse expert-insight?
  [

    ;note the list below sets three safeguarding dealt with offences (<13 sexual offences) to RESPONSE ONLY as we do not model safeguarding.

    (ifelse
      offence = "Murder"                                                                                      [ set requires-CID? true ]
      offence = "Corporate manslaughter"                                                                      [ set requires-CID? true ]
      offence = "Manslaughter"                                                                                [ set requires-CID? true ]
      offence = "Infanticide"                                                                                 [ set requires-CID? true ]
      offence = "Attempted murder"                                                                            [ set requires-CID? true ]
      offence = "Rape of a male child under 16"                                                               [ set requires-CID? true ]
      offence = "Rape of a female child under 16"                                                             [ set requires-CID? true ]
      offence = "Intentional destruction of a viable unborn child"                                            [ set requires-CID? true ]
      offence = "Rape of a Female - Multiple Undefined Offenders"                                             [ set requires-CID? true ]
      offence = "Rape of a female child under 13"                                                             [ set requires-CID? false ] ; Safeguarding response
      offence = "Rape of a male aged 16 and over"                                                             [ set requires-CID? true ]
      offence = "Rape of a Male - Multiple Undefined Offenders"                                               [ set requires-CID? true ]
      offence = "Rape of a female aged 16 and over"                                                           [ set requires-CID? true ]
      offence = "Rape of a male child under 13"                                                               [ set requires-CID? false ]
      offence = "Aggravated burglary in a dwelling (outcome only)"                                            [ set requires-CID? true ]
      offence = "Aggravated Burglary Residential"                                                             [ set requires-CID? true ]
      offence = "Assault with intent to cause serious harm"                                                   [ set requires-CID? true ]
      offence = "Conspiracy to murder"                                                                        [ set requires-CID? true ]
      offence = "Aggravated burglary in a building other than a dwelling(outcome only)"                       [ set requires-CID? true ]
      offence = "Aggravated Burglary Business and Community"                                                  [ set requires-CID? true ]
      offence = "Trafficking for sexual exploitation"                                                         [ set requires-CID? true ]
      offence = "Causing death by careless driving under influence of drink or drugs"                         [ set requires-CID? false ]
      offence = "Endangering life"                                                                            [ set requires-CID? true ]
      offence = "Sexual activity etc with a person with a mental disorder"                                    [ set requires-CID? true ]
      offence = "Other firearms offences"                                                                     [ set requires-CID? true ]
      offence = "Kidnapping"                                                                                  [ set requires-CID? true ]
      offence = "Sexual assault on a female child under 13"                                                   [ set requires-CID? false ]
      offence = "Incest or familial sexual offences"                                                          [ set requires-CID? true ]
      offence = "Modern slavery"                                                                              [ set requires-CID? true ]
      offence = "Procuring illegal abortion"                                                                  [ set requires-CID? true ]
      offence = "Causing sexual activity without consent"                                                     [ set requires-CID? true ]
      offence = "Other miscellaneous sexual offences"                                                         [ set requires-CID? true ]
      offence = "Causing death or serious injury by dangerous driving"                                        [ set requires-CID? false ]
      offence = "Causing or allowing death of child or vulnerable person"                                     [ set requires-CID? true ]
      offence = "Abuse of children through sexual exploitation"                                               [ set requires-CID? "Maybe" ]
      offence = "Sexual assault on a male child under 13"                                                     [ set requires-CID? false ]
      offence = "Arson endangering life"                                                                      [ set requires-CID? true ]
      offence = "Sexual activity involving a child under 13"                                                  [ set requires-CID? "Maybe" ]
      offence = "Aiding suicide"                                                                              [ set requires-CID? true ]
      offence = "Robbery of business property"                                                                [ set requires-CID? true ]
      offence = "Robbery of personal property"                                                                [ set requires-CID? true ]
      offence = "Blackmail"                                                                                   [ set requires-CID? true ]
      offence = "Sexual assault on a male aged 13 and over"                                                   [ set requires-CID? true ]
      offence = "Sexual activity involving child under 16"                                                    [ set requires-CID? true ]
      offence = "Possession of firearms with intent"                                                          [ set requires-CID? true ]
      offence = "Causing death by aggravated vehicle taking"                                                  [ set requires-CID? true ]
      offence = "Trafficking in controlled drugs"                                                             [ set requires-CID? "Maybe" ]
      offence = "Burglary in a dwelling(outcome only)"                                                        [ set requires-CID? true ]
      offence = "Attempted burglary in a dwelling (outcome only)"                                             [ set requires-CID? true ]
      offence = "Distraction burglary in a dwelling (outcome only)"                                           [ set requires-CID? true ]
      offence = "Attempted distraction burglary in a dwelling (outcome only)"                                 [ set requires-CID? true ]
      offence = "Burglary Residential"                                                                        [ set requires-CID? true ]
      offence = "Attempted Burglary Residential"                                                              [ set requires-CID? true ]
      offence = "Distraction Burglary Residential"                                                            [ set requires-CID? true ]
      offence = "Attempted Distraction Burglary Residential"                                                  [ set requires-CID? true ]
      offence = "Sexual grooming"                                                                             [ set requires-CID? true ]
      offence = "Sexual assault on a female aged 13 and over"                                                 [ set requires-CID? true ]
      offence = "Possession of firearms offences"                                                             [ set requires-CID? true ]
      offence = "Assault with injury on a constable"                                                          [ set requires-CID? true ]
      offence = "Exploitation of prostitution"                                                                [ set requires-CID? true ]
      offence = "Violent disorder"                                                                            [ set requires-CID? true ]
      offence = "Racially or religiously aggravated assault with injury"                                      [ set requires-CID? false ]
      offence = "Child abduction"                                                                             [ set requires-CID? true ]
      offence = "Threats to kill"                                                                             [ set requires-CID? true ]
      offence = "Other knives offences"                                                                       [ set requires-CID? false ]
      offence = "Profiting from or concealing knowledge of the proceeds of crime"                             [ set requires-CID? true ]
      offence = "Wildlife"                                                                                    [ set requires-CID? false ]
      offence = "Abuse of position of trust of a sexual nature"                                               [ set requires-CID? "Maybe" ]
      offence = "Offender Management Act offences"                                                            [ set requires-CID? "Maybe" ]
      offence = "Concealing an infant death close to birth"                                                   [ set requires-CID? true ]
      offence = "Bigamy"                                                                                      [ set requires-CID? true ]
      offence = "Possession of false documents"                                                               [ set requires-CID? "Maybe" ]
      offence = "Absconding from lawful custody"                                                              [ set requires-CID? "Maybe" ]
      offence = "Assault with injury"                                                                         [ set requires-CID? true ]
      offence = "Arson not endangering life"                                                                  [ set requires-CID? "Maybe" ]
      offence = "Causing death by driving: unlicensed or disqualified or uninsured drivers"                   [ set requires-CID? false ]
      offence = "Other notifiable offences"                                                                   [ set requires-CID? "Maybe" ]
      offence = "Perverting the course of justice"                                                            [ set requires-CID? true ]
      offence = "Other forgery"                                                                               [ set requires-CID? true ]
      offence = "Cruelty to children/young persons"                                                           [ set requires-CID? true ]
      offence = "Obscene publications etc"                                                                    [ set requires-CID? true ]
      offence = "Making, supplying or possessing articles for use in fraud"                                   [ set requires-CID? "Maybe" ]
      offence = "Theft or unauthorised taking of motor vehicle"                                               [ set requires-CID? false ]
      offence = "Burglary in a building other than a dwelling (outcome only)"                                 [ set requires-CID? true ]
      offence = "Attempted burglary in a building other than a dwelling (outcome only)"                       [ set requires-CID? "Maybe" ]
      offence = "Burglary Business and Community"                                                             [ set requires-CID? "Maybe" ]
      offence = "Attempted Burglary Business and Community"                                                   [ set requires-CID? "Maybe" ]
      offence = "Dangerous driving"                                                                           [ set requires-CID? false ]
      offence = "Causing death by careless or inconsiderate driving"                                          [ set requires-CID? false ]
      offence = "Theft from automatic machine or meter"                                                       [ set requires-CID? false ]
      offence = "Perjury"                                                                                     [ set requires-CID? true ]
      offence = "Theft of mail"                                                                               [ set requires-CID? false ]
      offence = "Theft from the person"                                                                       [ set requires-CID? "Maybe" ]
      offence = "Other offences against the State or public order"                                            [ set requires-CID? "Maybe" ]
      offence = "Threat or possession with intent to commit criminal damage"                                  [ set requires-CID? false ]
      offence = "Stalking"                                                                                    [ set requires-CID? "Maybe" ]
      offence = "Handling stolen goods"                                                                       [ set requires-CID? "Maybe" ]
      offence = "Aggravated vehicle taking"                                                                   [ set requires-CID? "Maybe" ]
      offence = "Possession of article with blade or point"                                                   [ set requires-CID? false ]
      offence = "Possession of other weapons"                                                                 [ set requires-CID? false ]
      offence = "Unnatural sexual offences"                                                                   [ set requires-CID? true ]
      offence = "Theft in a dwelling other than from an automatic machine or meter"                           [ set requires-CID? false ]
      offence = "Theft by an employee"                                                                        [ set requires-CID? "Maybe" ]
      offence = "Exposure and voyeurism"                                                                      [ set requires-CID? "Maybe" ]
      offence = "Racially or religiously aggravated harassment"                                               [ set requires-CID? "Maybe" ]
      offence = "Other theft"                                                                                 [ set requires-CID? "Maybe" ]
      offence = "Harassment"                                                                                  [ set requires-CID? "Maybe" ]
      offence = "Theft from vehicle"                                                                          [ set requires-CID? "Maybe" ]
      offence = "Forgery or use of false drug prescription"                                                   [ set requires-CID? "Maybe" ]
      offence = "Going equipped for stealing, etc"                                                            [ set requires-CID? "Maybe" ]
      offence = "Racially or religiously aggravated assault without injury"                                   [ set requires-CID? false ]
      offence = "Theft or unauthorised taking of a pedal cycle"                                               [ set requires-CID? false ]
      offence = "Malicious Communications"                                                                    [ set requires-CID? "Maybe" ]
      offence = "Racially or religiously aggravated criminal damage"                                          [ set requires-CID? false ]
      offence = "Assault without injury"                                                                      [ set requires-CID? "Maybe" ]
      offence = "Disclosure, obstruction, false or misleading statements etc"                                 [ set requires-CID? "Maybe" ]
      offence = "Racially or religiously aggravated public fear, alarm or distress"                           [ set requires-CID? false ]
      offence = "Shoplifting"                                                                                 [ set requires-CID? false ]
      offence = "Interfering with a motor vehicle"                                                            [ set requires-CID? false ]
      offence = "Other drug offences"                                                                         [ set requires-CID? true ]
      offence = "Possession of controlled drugs (excl. Cannabis)"                                             [ set requires-CID? "Maybe" ]
      offence = "Assault without injury on a constable"                                                       [ set requires-CID? "Maybe" ]
      offence = "Fraud, forgery etc associated with vehicle or driver records"                                [ set requires-CID? false ]
      offence = "Making off without payment"                                                                  [ set requires-CID? false ]
      offence = "Public fear, alarm or distress"                                                              [ set requires-CID? false ]
      offence = "Criminal damage to a dwelling"                                                               [ set requires-CID? false ]
      offence = "Criminal damage to a building other than a dwelling"                                         [ set requires-CID? false ]
      offence = "Criminal damage to a vehicle"                                                                [ set requires-CID? false ]
      offence = "Other criminal damage"                                                                       [ set requires-CID? "Maybe" ]
      offence = "Dishonest use of electricity"                                                                [ set requires-CID? false ]
      offence = "Soliciting for the purposes of prostitution"                                                 [ set requires-CID? false ]
      offence = "Bail offences"                                                                               [ set requires-CID? "Maybe" ]
      offence = "Possession of controlled drugs (Cannabis)"                                                   [ set requires-CID? "Maybe" ]
      offence = "Anti-social behaviour"                                                                       [ set requires-CID? false ]
    )
      ; if maybe requires CID toss a coin
      if requires-CID? = "Maybe" [ ifelse random-float 1 > 0.5 [ set requires-CID? true ] [ set requires-CID? false ] ]

    ]

    [

      ; No expert insight - arbitrarily cut at 1000 severity
      ifelse event-severity >= 1000 [ set requires-CID? true ] [ set requires-CID? false ]


    ]

  ;print (word "Establishing CID requirements - expert insight = "  expert-insight? " offence = " offence " severity = " event-severity " --- requires CID? " requires-CID? )

    report requires-CID?

end










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
190
350
463
995
-1
-1
26.5
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
9
0
23
0
0
1
ticks
30.0

BUTTON
10
15
77
48
setup
\nsetup\n
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

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
610
835
790
880
Response Officers Available
count resources with [resource-status = ON-DUTY-AVAILABLE and resource-type = RESPONSE]
17
1
11

MONITOR
1105
830
1245
875
Events - Awaiting
count events with [event-status = AWAITING-SUPPLY]
17
1
11

MONITOR
1250
830
1390
875
Events - Ongoing
count events with [event-status = ONGOING]
17
1
11

MONITOR
1395
830
1530
875
Events - Completed
count-completed-events
17
1
11

PLOT
490
160
1135
280
% Resource Usage
time
%
0.0
10.0
0.0
100.0
true
true
"" ""
PENS
"CID" 1.0 0 -2674135 true "" ""
"RESPONSE" 1.0 0 -13345367 true "" ""

PLOT
490
290
1665
549
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
210
75
335
152
Shifts:\n1. 0700 - 1700\n2. 1400 - 2400\n3. 2200 - 0700
15
0.0
1

MONITOR
190
15
330
60
Current DateTime
time:show dt \"dd-MM-yyyy HH:mm\"
17
1
11

PLOT
490
560
1665
817
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
865
175
898
VERBOSE
VERBOSE
1
1
-1000

MONITOR
800
835
1000
880
Response Officers Responding
count resources with [resource-status = ON-DUTY-RESPONDING and resource-type = RESPONSE]
17
1
11

PLOT
1060
970
1665
1090
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
"waiting-1" 1.0 0 -2674135 true "" ""
"waiting-2" 1.0 0 -955883 true "" ""
"waiting-3" 1.0 0 -1184463 true "" ""

SWITCH
10
310
175
343
event-file-out
event-file-out
0
1
-1000

MONITOR
1105
880
1245
925
priority 1 waiting
count events with [event-status = AWAITING-SUPPLY and event-priority = 1]
17
1
11

MONITOR
1250
880
1390
925
priority 2 waiting
count events with [event-status = AWAITING-SUPPLY and event-priority = 2]
17
1
11

MONITOR
1395
880
1530
925
priority 3 waiting
count events with [event-status = AWAITING-SUPPLY and event-priority = 3]
17
1
11

PLOT
490
25
1135
150
Crime
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
"total" 1.0 0 -16777216 true "" ""

BUTTON
10
825
175
860
close files
close-files
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
275
175
308
replication
replication
1
100
6.0
1
1
NIL
HORIZONTAL

MONITOR
338
15
458
60
Shift1-Shift2-Shift3
(word Shift-1 \"-\" Shift-2 \"-\" Shift-3)
17
1
11

CHOOSER
15
95
175
140
Force
Force
"Avon and Somerset" "Bedfordshire" "Cambridgeshire" "Cheshire" "Cleveland" "Cumbria" "Derbyshire" "Devon and Cornwall" "Dorset" "Durham" "Dyfed-Powys" "Essex" "Gloucestershire" "Greater Manchester" "Gwent" "Hampshire" "Hertfordshire" "Humberside" "Kent" "Lancashire" "Leicestershire" "Lincolnshire" "City of London" "Merseyside" "Metropolitan Police" "Norfolk" "North Wales" "North Yorkshire" "Northamptonshire" "Northumbria" "Nottinghamshire" "South Wales" "South Yorkshire" "Staffordshire" "Suffolk" "Surrey" "Sussex" "Thames Valley" "Warwickshire" "West Mercia" "West Midlands" "West Yorkshire" "Wiltshire" "TEST"
9

INPUTBOX
15
145
80
205
StartYear
2021.0
1
0
Number

CHOOSER
85
145
177
190
StartMonth
StartMonth
1 2 3 4 5 6 7 8 9 10 11 12
0

SWITCH
10
235
175
268
SetSeed
SetSeed
0
1
-1000

SLIDER
204
155
344
188
shift-1-response
shift-1-response
0
300
50.0
5
1
NIL
HORIZONTAL

SLIDER
204
190
344
223
shift-2-response
shift-2-response
0
300
50.0
5
1
NIL
HORIZONTAL

SLIDER
204
225
344
258
shift-3-response
shift-3-response
0
300
50.0
5
1
NIL
HORIZONTAL

SLIDER
349
155
454
188
shift-1-CID
shift-1-CID
0
100
30.0
5
1
NIL
HORIZONTAL

SLIDER
349
190
454
223
shift-2-CID
shift-2-CID
0
100
30.0
5
1
NIL
HORIZONTAL

SLIDER
349
225
454
258
shift-3-CID
shift-3-CID
0
100
30.0
5
1
NIL
HORIZONTAL

MONITOR
350
105
455
150
Total Resources
shift-1-response + shift-2-response + shift-3-response + shift-1-CID + shift-2-CID + shift-3-CID
17
1
11

BUTTON
350
70
455
103
visualise-shifts
ask resources with [working-shift = 1] \n[\nifelse (size = 0.7) \n[set size 1 set plabel \"\" ] \n[set size 0.7 set plabel 1]\n]\nask resources with [working-shift = 2] \n[\nifelse (size = 0.7) \n[set size 1 set plabel \"\" ] \n[set size 0.7 set plabel 2]\n]\n\nask resources with [working-shift = 3]\n[\nifelse (size = 0.7) \n[set size 1 set plabel \"\" ] \n[set size 0.7 set plabel 3]\n]
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
522
842
597
860
Resources
13
0.0
1

TEXTBOX
1040
841
1095
859
Events
13
0.0
1

TEXTBOX
1033
886
1093
904
Backlog
13
0.0
1

MONITOR
610
970
880
1015
Response - mean #jobs completed p/officer
mean [events-completed] of resources with [resource-type = RESPONSE]
3
1
11

MONITOR
610
1020
880
1065
CID - mean #jobs completed p/officer
mean [events-completed] of resources with [resource-type = CID]
3
1
11

MONITOR
610
885
790
930
CID Officers Available
count resources with [resource-status = ON-DUTY-AVAILABLE and resource-type = CID]
17
1
11

MONITOR
800
885
1000
930
CID Officers Responding
count resources with [resource-status = ON-DUTY-RESPONDING and resource-type = CID]
17
1
11

MONITOR
895
970
1035
1015
Average CID Workload
mean [(count current-event)] of resources with [resource-type = CID]
3
1
11

MONITOR
895
1020
1035
1065
Max CID Workload 
max [(count current-event)] of resources with [(resource-status = ON-DUTY-AVAILABLE or resource-status = ON-DUTY-RESPONDING) and resource-type = CID]
17
1
11

MONITOR
895
1070
1035
1115
Min CID Workload
min [(count current-event)] of resources with [(resource-status = ON-DUTY-AVAILABLE or resource-status = ON-DUTY-RESPONDING) and resource-type = CID]
17
1
11

PLOT
1145
160
1665
280
CID Mean Workload
NIL
NIL
0.0
10.0
0.0
5.0
true
true
"" ""
PENS
"Workload" 1.0 0 -16777216 true "" "plot mean [(count current-event)] of resources with [resource-type = CID]"

SWITCH
10
905
175
938
show-workload
show-workload
1
1
-1000

SLIDER
5
410
180
443
non-crime-%-CID
non-crime-%-CID
0
1
0.5
0.01
1
NIL
HORIZONTAL

SLIDER
5
445
180
478
non-crime-%-RESPONSE
non-crime-%-RESPONSE
0
1
0.5
0.01
1
NIL
HORIZONTAL

SWITCH
206
267
451
300
response-safe-crewing-DAY
response-safe-crewing-DAY
1
1
-1000

SWITCH
206
307
453
340
response-safe-crewing-NIGHT
response-safe-crewing-NIGHT
0
1
-1000

SWITCH
10
945
175
978
HEADLESS
HEADLESS
0
1
-1000

SWITCH
210
970
455
1003
RESPONSE-RESOURCE-LINEAR
RESPONSE-RESOURCE-LINEAR
0
1
-1000

SWITCH
210
1005
455
1038
CID-RESOURCE-LINEAR
CID-RESOURCE-LINEAR
1
1
-1000

SWITCH
210
935
455
968
Expert-CID-Allocation
Expert-CID-Allocation
0
1
-1000

PLOT
1145
25
1665
150
Events Ongoing
Ongoing Events
NIL
0.0
10.0
0.0
10.0
true
true
"" ""
PENS
"CID-Ongoing" 1.0 0 -2674135 true "" ""
"RESPONSE-Ongoing" 1.0 0 -13345367 true "" ""

TEXTBOX
520
975
590
993
Workload
13
0.0
1

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
NetLogo 6.2.0
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
