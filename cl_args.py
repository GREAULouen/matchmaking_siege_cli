import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Matchmaking Simulation CLI Tool"
    )


    parser.add_argument(
        "--sim-time",
        type=float,
        default=3600,
        help="Total simulation time in seconds (default: 3600)"
    )


    parser.add_argument(
        "--num-players",
        type=int,
        default=5000,
        help="Number of players in the simulation (default: 5000)"
    )


    parser.add_argument(
        "--elo-strategy",
        type=str,
        default="naive",
        choices=["naive"],
        help="ELO strategy to use (default: naive)"
    )


    parser.add_argument(
        "--mm-strategy",
        type=str,
        default="naive",
        choices=["naive"],
        help="Matchmaking strategy to use (default: naive)"
    )


    parser.add_argument(
        "--log-file",
        type=str,
        default="matchmaking_stats.log",
        help="File to which stats are logged (default: matchmaking_stats.log)"
    )


    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )


    parser.add_argument(
        "--sim-config",
        type=str,
        default="simulation_config.json",
        help="Simulation configuration file (default: simulation_config.json)"
    )

    return parser.parse_args()
