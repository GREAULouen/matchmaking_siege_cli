#!/usr/bin/env python3
import random
import heapq
from statistics import mean
from cl_args import parse_arguments

class Player:
    def __init__(self, pid, elo):
        self.id = pid
        self.elo = elo
        self.in_game = False
        self.in_queue = False
        self.last_queue_join_time = None

def schedule_event(event_queue, event_time, event_type, event_data):
    heapq.heappush(event_queue, (event_time, event_type, event_data))

def check_matchmaking(queue_type, current_time, queues, players, event_queue, stats, sim_params):
    if queue_type == "1v1":
        q = queues["1v1"]
        # While there are at least two players waiting, form a match.
        while len(q) >= 2:
            p1 = q.pop(0)
            players[p1['player_id']].in_queue = False
            p2 = q.pop(0)
            players[p2['player_id']].in_queue = False

            # Record waiting times for both players.
            wait1 = current_time - p1['join_time']
            wait2 = current_time - p2['join_time']
            stats["1v1"]["wait_times"].extend([wait1, wait2])

            # Record average Elo (from pre–game Elo values).
            avg_elo = (players[p1['player_id']].elo + players[p2['player_id']].elo) / 2
            stats["1v1"]["avg_elos"].append(avg_elo)

            # Mark both players as now in a game.
            players[p1['player_id']].in_game = True
            players[p2['player_id']].in_game = True

            # Schedule a game finish event.
            game_duration = random.uniform(sim_params["game_min_duration"], sim_params["game_max_duration"])
            schedule_event(event_queue, current_time + game_duration, "game_finish", {
                "players": [p1['player_id'], p2['player_id']],
                "queue_type": "1v1"
            })
    elif queue_type == "group":
        q = queues["group"]
        # Form a match as soon as there are at least group_min players.
        while len(q) >= sim_params["group_min"]:
            # If there are 10 or fewer waiting, match them all; otherwise, take the first 10.
            if len(q) <= sim_params["group_max"]:
                match_list = [q.pop(0) for _ in range(len(q))]
            else:
                match_list = [q.pop(0) for _ in range(sim_params["group_max"])]
            for item in match_list:
                players[item['player_id']].in_queue = False
                wait = current_time - item['join_time']
                stats["group"]["wait_times"].append(wait)
            avg_elo = mean([players[item['player_id']].elo for item in match_list])
            stats["group"]["avg_elos"].append(avg_elo)
            # Mark players as in a game.
            for item in match_list:
                players[item['player_id']].in_game = True
            game_duration = random.uniform(sim_params["game_min_duration"], sim_params["game_max_duration"])
            schedule_event(event_queue, current_time + game_duration, "game_finish", {
                "players": [item['player_id'] for item in match_list],
                "queue_type": "group"
            })

def process_game_finish(event_data, current_time, players, event_queue, sim_params):
    queue_type = event_data["queue_type"]
    player_ids = event_data["players"]
    if queue_type == "1v1":
        # For a duel, randomly select a winner.
        winner = random.choice(player_ids)
        loser = player_ids[0] if player_ids[1] == winner else player_ids[1]
        players[winner].elo += sim_params["duel_win_bonus"]
        players[loser].elo -= sim_params["duel_loss_penalty"]
    elif queue_type == "group":
        # For a group game, randomly select one winner.
        winner = random.choice(player_ids)
        players[winner].elo += sim_params["group_win_bonus"]
        for pid in player_ids:
            if pid != winner:
                players[pid].elo -= sim_params["group_loss_penalty"]
    # Mark players as free and schedule their next join event.
    for pid in player_ids:
        players[pid].in_game = False
        next_join = current_time + random.uniform(sim_params["min_wait_before_requeue"], sim_params["max_wait_before_requeue"])
        schedule_event(event_queue, next_join, "join_queue", {
            "player_id": pid,
            "queue_type": random.choice(["1v1", "group"])
        })

def run_simulation(sim_time, num_players, elo_strategy, mm_strategy, log_file, seed):
    # Set random seed if provided.
    if seed is not None:
        random.seed(seed)

    # Simulation parameters (can be adjusted or extended for other strategies).
    sim_params = {
        "game_min_duration": 30,        # Minimum game duration (seconds)
        "game_max_duration": 90,        # Maximum game duration (seconds)
        "min_wait_before_requeue": 5,   # Minimum wait after finishing a game
        "max_wait_before_requeue": 30,  # Maximum wait after finishing a game
        "duel_win_bonus": 20,           # Elo bonus for winning a duel
        "duel_loss_penalty": 20,        # Elo penalty for losing a duel
        "group_min": 6,                 # Minimum players needed for a group match
        "group_max": 10,                # Maximum players in a group match
        "group_win_bonus": 10,          # Elo bonus for winning a group game
        "group_loss_penalty": 5         # Elo penalty for losing a group game
    }

    # Initialize players with Elo values drawn from a normal distribution.
    players = [Player(pid, random.gauss(1500, 100)) for pid in range(num_players)]

    # Initialize event queue: each event is a tuple (time, event_type, event_data).
    event_queue = []
    # Schedule an initial join event for every player.
    for player in players:
        initial_join = random.uniform(0, sim_time * 0.1)
        schedule_event(event_queue, initial_join, "join_queue", {
            "player_id": player.id,
            "queue_type": random.choice(["1v1", "group"])
        })

    # Queues for matchmaking.
    queues = {
        "1v1": [],
        "group": []
    }

    # Stats collection per queue.
    stats = {
        "1v1": {"wait_times": [], "avg_elos": []},
        "group": {"wait_times": [], "avg_elos": []}
    }

    current_time = 0
    # Main simulation loop: process events until the simulation time is reached.
    while event_queue and current_time <= sim_time:
        event_time, event_type, event_data = heapq.heappop(event_queue)
        current_time = event_time
        if current_time > sim_time:
            break

        if event_type == "join_queue":
            pid = event_data["player_id"]
            qtype = event_data["queue_type"]
            # Only add the player if they aren’t already in a game or in a queue.
            if not players[pid].in_game and not players[pid].in_queue:
                players[pid].in_queue = True
                players[pid].last_queue_join_time = current_time
                queues[qtype].append({"player_id": pid, "join_time": current_time})
                # Immediately try to match players in this queue.
                check_matchmaking(qtype, current_time, queues, players, event_queue, stats, sim_params)
        elif event_type == "game_finish":
            process_game_finish(event_data, current_time, players, event_queue, sim_params)

    # Compile final stats per queue.
    results = {}
    for q in ["1v1", "group"]:
        if stats[q]["wait_times"]:
            results[q] = {
                "mean_wait": mean(stats[q]["wait_times"]),
                "min_wait": min(stats[q]["wait_times"]),
                "max_wait": max(stats[q]["wait_times"]),
                "mean_avg_elo": mean(stats[q]["avg_elos"]) if stats[q]["avg_elos"] else None,
                "min_avg_elo": min(stats[q]["avg_elos"]) if stats[q]["avg_elos"] else None,
                "max_avg_elo": max(stats[q]["avg_elos"]) if stats[q]["avg_elos"] else None,
                "matches": len(stats[q]["avg_elos"])
            }
        else:
            results[q] = {}

    # Append the stats to the log file (CSV format).
    with open(log_file, "a") as f:
        for q in results:
            if results[q]:
                f.write(f"{elo_strategy},{mm_strategy},{q},{results[q]['matches']},{results[q]['mean_wait']:.2f},"
                        f"{results[q]['min_wait']:.2f},{results[q]['max_wait']:.2f},{results[q]['mean_avg_elo']:.2f},"
                        f"{results[q]['min_avg_elo']:.2f},{results[q]['max_avg_elo']:.2f},{sim_time}\n")

    # Print the results.
    print("Simulation Results:")
    for q in results:
        if results[q]:
            print(f"\nQueue: {q}")
            print(f"  Matches: {results[q]['matches']}")
            print(f"  Wait Time (sec): Mean = {results[q]['mean_wait']:.2f}, "
                  f"Min = {results[q]['min_wait']:.2f}, Max = {results[q]['max_wait']:.2f}")
            print(f"  Average Elo: Mean = {results[q]['mean_avg_elo']:.2f}, "
                  f"Min = {results[q]['min_avg_elo']:.2f}, Max = {results[q]['max_avg_elo']:.2f}")
        else:
            print(f"\nQueue: {q} - No matches formed.")
    return results

def main():
    args = parse_arguments()

    run_simulation(
        args.sim_time,
        args.num_players,
        args.elo_strategy,
        args.mm_strategy,
        args.log_file,
        args.seed
    )

if __name__ == "__main__":
    main()
