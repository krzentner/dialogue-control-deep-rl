import re


def nlu(input):
    input = input.lower()
    command = None
    
    # (1st level) skip
    skip = re.search("skip|don't move|do not move|hold position|stay|stop", input, re.I)
    
    # (1st level) go to any direction
    # filter out "alright", "yes, right"
    go_direction = re.search('(?:.*[^,s] )(right|left|up|down|top|bottom)', input, re.I)
    
    # (1st level) use item
    # only support "use *", "use the *"
    use_item = re.search('(?:.*(?:use |use the ))(ruby|gold|amethyst|diamond|silver|jade|coal|pearl)', input, re.I)
    
    # (2nd level) request item
    # need to deal with 2 cases: "I need/want *", "Can you *"
    request_item = re.search("(?:.*"
                              "(?:(?:^| )i (?:[^\s]* ){0,2}(?:need|want) (?:[^\s]* ){0,2})"
                              "|"
                              "(?:(?:can|could) you (?:[^\s]* ){0,4})"
                             ")(ruby|gold|amethyst|diamond|silver|jade|coal|pearl)", input, re.I)
    
    # (2nd level) offer item
    # need to deal with 2 cases: "Do you need/want *", "I can *"
    offer_item = re.search("(?:.*"
                            "(?:you (?:[^\s]* ){0,2}(?:need|want) (?:[^\s]* ){0,2})"
                            "|"
                            "(?:i can (?:[^\s]* ){0,4})"
                           ")(ruby|gold|amethyst|diamond|silver|jade|coal|pearl)", input, re.I)
    
    # (2nd level) accept offer
    # "it's/that's/this is/it'd be/it's really good/ok/alright" 
    # "thanks/thank you/sure/no problem" 
    # !!"no/nope/no thanks/no need"
    accept_offer = re.search("(?:(?:s|be|really) (?:ok|alright|good)|thank|sure|no problem)", input, re.I)
    if re.search("(^| )no(?! problem)", input, re.I):
        accept_offer = None
    
    # (2nd level) decline offer
    # "no/no need/nope/don't/do not"
    decline_offer = re.search("(^| )no(?! problem)"
                              "|n't"
                              "|do not", input, re.I)
    
    # (3rd level) request goal
    # "what's your goal/what do you plan to do/what are you planning/what do you want"
    request_goal = re.search("your goal"
                             "|you (?:[^\s]* ){0,2}plan to (?:do|make|craft|build)"
                             "|what (?:[^\s]* ){0,3}you (?:want|need)"
                             "|re you (?:trying|planning|doing|making|crafting|building)", input, re.I)
    
    # (3rd level) give goal
    # "my goal is/I plan/I want/I need/I'm building" + "crown|bracelet|ring"
    # If gem, metal, shape all specified, set REQUEST_ITEM and OFFER_ITEM to false
    # give_goal = bool(re.search("my goal"
                               # "|I (?:[^\s]* ){0,2}plan to (?:do|make|craft|build)"
                               # "|I (?:[^\s]* ){0,2}(?:want|need)"
                               # "|m (?:trying|planning|doing|making|crafting|building)", input, re.I)) \
                # and bool(re.search("(?:crown|bracelet|ring)", input, re.I))
    
    # Actually, if gem, metal, shape are all specified, it is GIVE_GOAL or CONFIRM_GOAL
    give_goal = None
    gem = re.search("(ruby|amethyst|diamond|jade|coal|pearl)", input, re.I)
    metal = re.search("(gold|silver)", input, re.I)
    shape = re.search("(crown|bracelet|ring)", input, re.I)
    if gem and metal and shape:
        give_goal = True
        request_item = None
        offer_item = None
    
    # (3rd level) confirm goal
    # if contains "you" and none of "can you/do you/are you" appears, it's CONFIRM_GOAL
    confirm_goal = re.search("(?!can |do |are )you ", input, re.I)
    if confirm_goal and gem and metal and shape:
        confirm_goal = True
        give_goal = None
    
    # (3rd level) goal_confirmed
    goal_confirmed = re.search("(yeah|yes|right|exact|correct)", input, re.I)
    
    
    if skip:
        command = "skip()"
    
    elif go_direction:
        direction = go_direction.groups()[0]
        direction = "up" if direction == "top" else direction
        direction = "down" if direction == "bottom" else direction
        command = "go({0})".format(direction)
    
    elif use_item:
        command = "use({0})".format(use_item.groups()[0])
    
    elif request_item:
        command = "request({0})".format(request_item.groups()[0])
    
    elif offer_item:
        command = "offer({0})".format(offer_item.groups()[0])
    
    elif accept_offer:
        command = "accept_offer()"
    
    elif decline_offer:
        command = "decline_offer()"
    
    elif request_goal:
        command = "request_goal()"
    
    elif give_goal:
        command = "give_goal({0},{1},{2})".format(metal.groups()[0], gem.groups()[0], shape.groups()[0])
    
    elif confirm_goal:
        command = "confirm_goal({0},{1},{2})".format(metal.groups()[0], gem.groups()[0], shape.groups()[0])
    
    elif goal_confirmed:
        command = "goal_confirmed()"
    
    else:
        command = "invalid_input()"
    
    return command



def nlg(command):
    command, params = re.split('[()]', command)[:2]
    if command == "accept_action":
        return("OK.")
    
    elif command == "decline_action":
        return("Sorry I can not do that!")
    
    elif command == "request_item":
        return("Can you bring {0} for me?".format(params))
    
    elif command == "offer_item":
        return("I can bring {0} for you.".format(params))
    
    elif command == "accept_request":
        return("OK, I can do that.")
    
    elif command == "decline_request":
        return("Sorry, I can not do that!")
    
    elif command == "accept_offer":
        return("That's good!")
    
    elif command == "decline_offer":
        return("No thanks.")
    
    elif command == "request_goal":
        return("Can you tell me what's your goal?")
    
    elif command == "give_goal":
        params = params.split(',')
        return("I want to make a {0} {1} with {2}.".format(params[0], params[2], params[1]))
    
    elif command == "confirm_goal":
        params = params.split(',')
        return("You want to make a {0} {1} with {2}. Is that correct?".format(params[0], params[2], params[1]))
    
    elif command == "goal_confirmed":
        return("Yes, that's right.")
        
    else:
        # not implemented
        assert False
        


if __name__=="__main__":
    print("#"*87)
    print("#"*40, " NLU ", "#"*40)
    print("#"*87)
    print("don't move", "\t\t", nlu("don't move"))
    print("hold position", "\t\t", nlu("hold position"))
    print()
    print("go top", "\t\t", nlu("go top"))
    print("turn right", "\t\t", nlu("turn right"))
    print()
    print("Alright", "\t\t", nlu("Alright"))
    print("Yes, right", "\t\t", nlu("Yes, right"))
    print()
    print("now use jade", "\t\t", nlu("now use jade"))
    print("use the gold", "\t\t", nlu("use the gold"))
    print()
    print("I really need the silver", "\t\t", nlu("I really need the silver"))
    print("Can you please go get ruby for me?", "\t\t", nlu("Can you please go get ruby for me?"))
    print()
    print("do you want silver?", "\t\t", nlu("do you want silver?"))
    print("I can go get the ruby for you", "\t\t", nlu("I can go get the ruby for you"))
    print()
    print("it's ok", "\t\t", nlu("it's ok"))
    print("that is good", "\t\t", nlu("that is good"))
    print("sure", "\t\t", nlu("sure"))
    print("yeah, thanks", "\t\t", nlu("yeah, thanks"))
    print("no problem", "\t\t", nlu("no problem"))
    print()
    print("no, thanks", "\t\t", nlu("no, thanks"))
    print("I don't need that", "\t\t", nlu("I don't need that"))
    print("Do not do that", "\t\t", nlu("Do not do that"))
    print()
    print("what's your goal", "\t\t", nlu("what's your goal"))
    print("what are you planning", "\t\t", nlu("what are you planning"))
    print("what do you want", "\t\t", nlu("what do you want"))
    print()
    print("I want to make silver crown with ruby", "\t\t", nlu("I want to make silver crown with ruby"))
    print("my goal is gold diamond ring", "\t\t", nlu("my goal is gold diamond ring"))
    print()
    print("So you wanna silver crown with ruby?", "\t\t", nlu("So you wanna silver crown with ruby?"))
    print("You are trying to make gold diamond ring", "\t\t", nlu("You are trying to make gold diamond ring"))
    print()
    print("that's correct", "\t\t", nlu("that's correct"))
    print("exactly", "\t\t", nlu("exactly"))
    print()
    print("I am the lord here, bow before me!", "\t\t", nlu("hey man what's up"))
    
    
    print()
    print()
    print("#"*87)
    print("#"*40, " NLG ", "#"*40)
    print("#"*87)
    print("accept_action()", "\t\t", nlg("accept_action()"))
    print("decline_action()", "\t\t", nlg("decline_action()"))
    print("request_item(gold)", "\t\t", nlg("request_item(gold)"))
    print("offer_item(silver)", "\t\t", nlg("offer_item(silver)"))
    print("accept_request()", "\t\t", nlg("accept_request()"))
    print("decline_request()", "\t\t", nlg("decline_request()"))
    print("accept_offer()", "\t\t", nlg("accept_offer()"))
    print("decline_offer()", "\t\t", nlg("decline_offer()"))
    print("request_goal()", "\t\t", nlg("request_goal()"))
    print("give_goal(silver,ruby,crown)", "\t\t", nlg("give_goal(silver,ruby,crown)"))
    print("confirm_goal(gold,diamond,ring)", "\t\t", nlg("confirm_goal(gold,diamond,ring)"))
    print("goal_confirmed()", "\t\t", nlg("goal_confirmed()"))
