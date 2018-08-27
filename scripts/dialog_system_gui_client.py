#!/usr/bin/env python

from bwi_msgs.srv import QuestionDialog
import rospy
import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))
from agent.simulator import Simulator
import time
import datetime
from actionlib_msgs.msg import *
from geometry_msgs.msg import Twist
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal


class DialogManager(Simulator):

    def __init__(self):
        super().__init__(uniform_init_belief = uniform_init_belief, 
        auto_state = auto_state, 
        auto_observations = auto_observations, # was true
        print_flag = print_flag, 
        policy_file = policy_file, 
        pomdp_file =  pomdp_file,
        policy_file_plus = policy_file_plus,
        pomdp_file_plus = policy_file_plus,
        trials_num = trials_num,
        num_task = num_task, 
        num_patient = num_patient, 
        num_recipient = num_recipient,
        belief_threshold = belief_threshold,
        ent_threshold = ent_threshold)

        self.item = ''
        self.person = ''
        self.deliver = False
        self.item_location.x = 0 # item location (vending machine for eg)
        self.item_location.y = 0
        self.person_location.x = 0  # delivery location
        self.person_location.y = 0

    def start_log(self):
        now = datetime.datetime.now().strftime("%I_%M%p_%B_%d_%Y")
        self.logfile = open("log_"+str(now)+".txt", 'w')
        self.counter = 0

    def get_string(self, question):
        rospy.wait_for_service('question_dialog')
        handle = rospy.ServiceProxy('question_dialog', QuestionDialog)
        response = handle(2, question, [], 200)
        self.print_message("thinking...")
        self.logfile.write("QUESTION: "+question+"\n")
        self.logfile.write("ANSWER: "+response.text+"\n")
        self.counter += 1
        return response.text.lower()

    def print_message(self, message):
        rospy.wait_for_service('question_dialog')
        handle = rospy.ServiceProxy('question_dialog', QuestionDialog)
        if 'EXECUTE:' in message:
            command = message.split()
            self.item = command[2]
            self.person = command[4]
            self.deliver = True
            print "item: ", item, " person: ", person

        response = handle(0, message, [], 0)
        self.logfile.write("MESSAGE: "+message+"\n")

    def close_log(self):
        self.logfile.write("\n Conversation Length: "+str(self.counter))
        self.logfile.close()

    def check_success(self):
        rospy.wait_for_service('question_dialog')
        handle = rospy.ServiceProxy('question_dialog', QuestionDialog)
        choices = ['Yes','No']
        response = handle(1, "The trial is now over.  Thank you for participating.  Please choose whether the robot chose the correct task to execute.",
                    choices, 200)
        self.print_message("Thank you.")
        self.logfile.write("SUCCESS: "+choices[response.index]+"\n")

    def move_to(self, location):
        print "moving to position: ", location
        ac = actionlib.SimpleActionClient("move_base", MoveBaseAction)

        while not ac.wait_for_server(rospy.Duration.from_sec(5.0)):
            rospy.loginfo("Waiting for move_base action server...")

        goal = MoveBaseGoal()

        #header
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()

        # point and orientation
        goal.target_pose.pose.position.x = location.x
        goal.target_pose.pose.position.y = location.y
        goal.target_pose.pose.position.z = 0
        goal.target_pose.pose.orientation.x = 0.0
        goal.target_pose.pose.orientation.y = 0.0
        goal.target_pose.pose.orientation.z = 0.0
        goal.target_pose.pose.orientation.w = 1.0

        rospy.loginfo("Sending Goal ...")
        ac.send_goal(goal)

    def wait_for_item_place(self):
        rospy.wait_for_service('question_dialog')
        handle = rospy.ServiceProxy('question_dialog', QuestionDialog)
        choices = ['OK']
        response = handle(1, "I need to deliver "+self.item+". Please place it on me and press 'OK'",
                    choices, 200)
        self.print_message("Thank you. Delivering.")

    def wait_for_item_pickup(self):
        rospy.wait_for_service('question_dialog')
        handle = rospy.ServiceProxy('question_dialog', QuestionDialog)
        choices = ['OK']
        response = handle(1, "I have "+self.item+" for "+self.person+". Please pick it up and press 'OK'",
                    choices, 200)
        self.print_message("Thank you. Delivery complete.")

    def demo_deliver(self):
        if self.deliver:
            move_to(item_location)
            wait_for_item_place()
            move_to(person_location)
            wait_for_item_pickup()
        else:
            print "Error in delivery.\n"


def main():
    # the number of variables are stored in this file for now
    f = open("../agent/data/num_config.txt")
    num = f.readline().split()

    s = DialogManager(uniform_init_belief = True, 
        auto_state = True, 
        auto_observations = False, # was true
        print_flag = False, 
        policy_file = 'main_new.policy', 
        pomdp_file =  'main_new.pomdp',
        policy_file_plus = 'main_plus_new.policy',
        pomdp_file_plus = 'main_plus_new.pomdp',
        trials_num = 1,
        num_task = int(num[0]), 
        num_patient = int(num[1]), 
        num_recipient = int(num[2]),
        belief_threshold = 0.4,
        ent_threshold = 2)
 
    if not s.uniform_init_belief:   
        print('note that initial belief is not uniform\n')

    ##s.run_numbers_of_trials()
    s.start_log()
    s.print_message("Hi, I am a service robot.  I can carry out delivery tasks.  You can tell me to bring an item to someone.")
    time.sleep(1)
    s.run()
    time.sleep(3)
    s.check_success()
    s.close_log()
    s.demo_deliver()

if __name__ == '__main__':
    main()
