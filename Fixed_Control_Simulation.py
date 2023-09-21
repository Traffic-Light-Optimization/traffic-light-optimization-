from sumo_rl.environment.env import SumoEnvironment
from config_files.greedy.action import greedy_action
from config_files.max_pressure.action import max_pressure_action
from config_files.action_lane_relationships import get_action_lane_relationships
from config_files.net_route_directories import get_file_locations
from config_files.observation_class_directories import get_observation_class
from config_files.custom_reward import my_reward_fn
import csv

type = "rand" #greedy, max_pressure, fixed, rand
observation = "camera" #camera, gps
map_name = "cologne1" #choose the map to simulate
map = get_file_locations(map_name) #obtain network, route, and additional files
gui = False #SUMO gui
num_seconds = 3600 #episode duration
delta_time = 5 #step duration
action_lanes = get_action_lane_relationships(map_name) #dict of relationships between actions and lanes for each intersection
seed = "12345"

# Selects the observation class specified
observation_class = get_observation_class(type, observation)

env = SumoEnvironment(
    net_file=map["net"],
    route_file=map["route"],
    use_gui=gui,
    num_seconds=num_seconds,
    delta_time=delta_time,
    sumo_seed=seed,
    observation_class=observation_class,
    reward_fn=my_reward_fn,
    additional_sumo_cmd=f"--additional-files {map['additional']}",
    fixed_ts = True if type == "fixed" else False,
    hide_cars = True if observation == "gps" else False
)

data = [] #initialize a list to store the data
observations = env.reset()
done = False
avg_rewards = []
while not done:
    if type == "greedy":
        actions = {agent: greedy_action(observations[agent], action_lanes[agent]) for agent in env.ts_ids}
    elif type == "max_pressure":
        actions = {agent: max_pressure_action(observations[agent], action_lanes[agent]) for agent in env.ts_ids}
    elif type == "fixed":
        actions = {}
    elif type == "rand":
        actions = {agent: env.action_spaces(agent).sample() for agent in env.ts_ids}
    else:
        raise ValueError(f"{type} is an invalid type for fixed control simulations")
    observations, rewards, dones, infos = env.step(actions)
    avg_rewards.append(sum(rewards.values())/len(rewards.values()))
    data.append(infos.copy())
    done = dones['__all__']

mean_reward = sum(avg_rewards)/len(avg_rewards)
print(f"Mean reward for simulation = {mean_reward}")

env.close()

# Create a CSV file and write the data to it
headings = data[0].keys()
if data:
    with open(f"./results/{type}/{map_name}-{observation}_conn1.csv", mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headings)
        writer.writeheader()
        writer.writerows(data)