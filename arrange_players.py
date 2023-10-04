import random

def rearrange_players(player_names):
    for i in range(0, len(player_names) - 1, 2):
        player_names[i], player_names[i + 1] = player_names[i + 1], player_names[i]
    return player_names



if __name__ == '__main__':
    players = ['Adams', 'Kyle', 'Jacob', 'Shrey']
    print(rearrange_players(players))
