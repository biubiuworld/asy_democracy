from otree.api import *
import random
import numpy as np
doc = """
This is a one-shot "Prisoner's Dilemma". Two players are asked separately
whether they want to cooperate or defect. Their choices directly determine the
payoffs.
"""


class C(BaseConstants):
    NAME_IN_URL = 'equalpay_asyvote'
    PLAYERS_PER_GROUP = 4
    NUM_ROUNDS = 8
    VOTE_ROUND = NUM_ROUNDS/2 + 1
    PAYOFF_DC_L = cu(60)
    PAYOFF_CC_L = cu(50)
    PAYOFF_DD_L = cu(40)
    PAYOFF_CD_L = cu(10)

    PAYOFF_DC_COOPERATE_L = cu(48)

    PAYOFF_DC_H = 2*PAYOFF_DC_L
    PAYOFF_CC_H = 2*PAYOFF_CC_L
    PAYOFF_DD_H = 2*PAYOFF_DD_L
    PAYOFF_CD_H = 2*PAYOFF_CD_L

    PAYOFF_DC_COOPERATE_H = 2*PAYOFF_DC_COOPERATE_L
    # RICH_ROLE = 'rich'
    # POOR_ROLE = 'poor'

    COST_VOTING = cu(10)


class Subsession(BaseSubsession):
    pass
    # def creating_session(subsession):
    #     if subsession.round_number == 1:
    #         subsession.group_randomly() #randomly group subjects in round 1
    #     else:
    #         subsession.group_like_round(1) #keep the same group structure as round 1


class Group(BaseGroup):
    treatment = models.StringField() #determine whether it is exoYES,...
    total_if_vote = models.IntegerField()
    total_shares = models.IntegerField()
    if_override = models.BooleanField() #whether computer overrides the group decision
    dice = models.BooleanField() #if computer overrides group decision, whether it is exoYES or exoNo


class Player(BasePlayer):
    cooperate = models.BooleanField(
        choices=[[True, 'Cooperate'], [False, 'Defect']],
        doc="""This player's decision""",
        widget=widgets.RadioSelect,
    )
    subgroup = models.StringField()
    opponent_id = models.IntegerField()
    player_role = models.StringField()

    if_vote = models.BooleanField(widget=widgets.RadioSelectHorizontal(),
                                  label='Do you want to vote for Game B?')
    additional_vote_share = models.IntegerField(label='How many additional shares you want to purchase?')
    individual_total_shares = models.IntegerField() #how many shares each have

    my_choice = models.StringField()
    opponent_type = models.StringField()
    opponent_choice = models.StringField()
    opponent_payoff = models.CurrencyField()

    game2_round = models.IntegerField()

    cum_payoff_game1 = models.CurrencyField()
    cum_payoff_game2 = models.CurrencyField()

    final_payoff = models.CurrencyField()



# FUNCTIONS
# def assign_role(group:Group):
#     rich = random.sample(group.get_players(), 2) #randomly choose two players as a pair in group A
#     poor = []
#     for p in group.get_players():
#         if p not in rich:
#             poor.append(p) #leave the rest of two as a pair in group B
#             p.player_role = 'poor'
#         else:
#             p.player_role = 'rich'


def random_match_in_pairs(group:Group):
    group1 = random.sample(group.get_players(), 2) #randomly choose two players as a pair in group A
    group2 = []
    for p in group.get_players():
        if p not in group1:
            group2.append(p) #leave the rest of two as a pair in group B
            p.subgroup = 'B'
        else:
            p.subgroup = 'A'
    # if group.round_number > 1:
    #     for p in group.get_players():
    #         p.player_role = p.in_round(p.round_number - 1).player_role

# def assign_same_role(group: Group):
#     for p in group.get_players():
#         p.player_role = p.in_round(p.round_number - 1)

def set_payoffs(group: Group):
    for p in group.get_players():
        set_payoff(p)


#get opponent id
def other_player(player: Player):
    for p in player.get_others_in_group():
        if p.subgroup == player.subgroup:
            player.opponent_id = p.id_in_group
    return player.opponent_id


def set_payoff(player: Player):
    # payoff_matrix_h = {
    #     (False, True): C.PAYOFF_DC_H,
    #     (True, True): C.PAYOFF_CC_H,
    #     (False, False): C.PAYOFF_DD_H,
    #     (True, False): C.PAYOFF_CD_H,
    # }

    payoff_matrix_l = {
        (False, True): C.PAYOFF_DC_L,
        (True, True): C.PAYOFF_CC_L,
        (False, False): C.PAYOFF_DD_L,
        (True, False): C.PAYOFF_CD_L,
    }
    # payoff_matrix_cooperate_h = {
    #     (False, True): C.PAYOFF_DC_COOPERATE_H,
    #     (True, True): C.PAYOFF_CC_H,
    #     (False, False): C.PAYOFF_DD_H,
    #     (True, False): C.PAYOFF_CD_H,
    # }

    payoff_matrix_cooperate_l = {
        (False, True): C.PAYOFF_DC_COOPERATE_L,
        (True, True): C.PAYOFF_CC_L,
        (False, False): C.PAYOFF_DD_L,
        (True, False): C.PAYOFF_CD_L,
    }

    other = player.group.get_player_by_id(other_player(player))
    if player.round_number < C.VOTE_ROUND:
        player.payoff = payoff_matrix_l[(player.cooperate, other.cooperate)]

        if player.round_number == 1:
            player.cum_payoff_game1 = player.payoff
        else:
            player.cum_payoff_game1 = player.in_round(player.round_number-1).cum_payoff_game1 + player.payoff
    else:
        if player.group.treatment == ('exoNo' or 'endoNo'):
            player.payoff = payoff_matrix_l[(player.cooperate, other.cooperate)]
        else:
            player.payoff = payoff_matrix_cooperate_l[(player.cooperate, other.cooperate)]

        if player.round_number == C.VOTE_ROUND:
            player.cum_payoff_game2 = player.payoff
        else:
            player.cum_payoff_game2 = player.in_round(player.round_number - 1).cum_payoff_game2 + player.payoff




def assign_treatment(group: Group):
    players = group.get_players()
    group_if_vote = [p.if_vote for p in players]
    group_individual_total_shares = [p.additional_vote_share+1 for p in players]
    group_if_vote = np.array(group_if_vote)
    group_individual_total_shares = np.array(group_individual_total_shares)
    total_if_vote = group_if_vote * group_individual_total_shares
    group.total_if_vote = round(sum(total_if_vote))
    group.total_shares = round(sum(group_individual_total_shares))

    if group.total_if_vote > group.total_shares/2:
        group.treatment = 'EndoYes'
    elif group.total_if_vote < group.total_shares/2:
        group.treatment = 'EndoNo'
    else:
        group.treatment = 'tie'
    computer_control = random.choices([1,0], weights=[1,1], k=1)
    if computer_control[0] == 1:
        group.if_override = 1
        dice = random.choices([1,0], weights=[1,1], k=1)
        if dice[0] == 1:
            group.dice = 1
            group.treatment = 'ExoYes'
        else:
            group.dice = 0
            group.treatment = 'ExoNo'
    else:
        group.if_override = 0

    if (group.treatment == 'tie') and (group.if_override == 0): #special case where a tie and not overriden by computer, computer randomly choose yes or no
        dice = random.choices([1, 0], weights=[1, 1], k=1)
        if dice[0] == 1:
            group.dice = 1
            group.treatment = 'EndoYes'
        else:
            group.dice = 0
            group.treatment = 'EndoNo'


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


# class AssignRoleWaitPage(WaitPage):
#     after_all_players_arrive = assign_role
#
#     @staticmethod
#     def is_displayed(player):
#         return player.round_number == 1


class Game1Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class MatchInPairsWaitPage(WaitPage):
    after_all_players_arrive = random_match_in_pairs


class Decision(Page):
    form_model = 'player'
    form_fields = ['cooperate']

    @staticmethod
    def is_displayed(player):
        return player.round_number < C.VOTE_ROUND

    # @staticmethod
    # def vars_for_template(player: Player):
    #     opponent = player.group.get_player_by_id(other_player(player))
    #     return dict(
    #         opponent=opponent,
    #     )


class VoteForGame2Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.VOTE_ROUND


class Vote(Page):
    form_model = 'player'
    form_fields = ['additional_vote_share', 'if_vote']

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.VOTE_ROUND

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            payoff_game1=player.in_round(C.VOTE_ROUND-1).cum_payoff_game1,
            share_limit=player.in_round(C.VOTE_ROUND-1).cum_payoff_game1//C.COST_VOTING,
        )

    @staticmethod
    def error_message(player: Player, values):
        if values['additional_vote_share'] >player.in_round(C.VOTE_ROUND-1).cum_payoff_game1//C.COST_VOTING:
            return 'Your purchase exceeds your limit!'

class VoteWaitPage(WaitPage):
    after_all_players_arrive = assign_treatment

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.VOTE_ROUND


class VoteResult(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.VOTE_ROUND

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            if_vote='Game B' if player.if_vote==1 else 'Game A',
            total_if_vote=player.group.total_if_vote,
            total_shares=player.group.total_shares,
            if_override='overrides' if player.group.if_override==1 else 'does not override',
            treatment='Game A' if player.group.treatment == ('exoNo' or 'endoNo') else 'Game B'
        )



class Game2Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.VOTE_ROUND


class DecisionAfterVote(Page):
    form_model = 'player'
    form_fields = ['cooperate']

    @staticmethod
    def is_displayed(player):
        return player.round_number >= C.VOTE_ROUND

    @staticmethod
    def vars_for_template(player: Player):
        player.group.treatment = player.group.in_round(C.VOTE_ROUND).treatment

        return dict(
            treatment=player.group.treatment,

        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        opponent = player.group.get_player_by_id(other_player(player))
        player.my_choice = player.field_display('cooperate')
        player.opponent_choice = opponent.field_display('cooperate')
        player.opponent_payoff = opponent.payoff
        player.game2_round = round(player.round_number - C.VOTE_ROUND + 1) if player.round_number >= C.VOTE_ROUND else 0
        return dict(
            opponent=opponent,
            same_choice=player.cooperate == opponent.cooperate,
            my_decision=player.field_display('cooperate'),
            opponent_decision=opponent.field_display('cooperate'),
            treatment=player.group.treatment if player.round_number>=C.VOTE_ROUND else None,
            before_vote_round=round(C.VOTE_ROUND-1),
            cum_payoff_game1=player.cum_payoff_game1 if player.round_number<C.VOTE_ROUND else 0,
            cum_payoff_game2=player.cum_payoff_game2 if player.round_number>=C.VOTE_ROUND else 0,
            player_all_rounds=player.in_all_rounds(),
            player_all_game1_rounds=player.in_rounds(1,round(C.VOTE_ROUND-1)),
            player_game2_rounds=player.in_rounds(C.VOTE_ROUND, player.round_number) if player.round_number>=C.VOTE_ROUND else 0,
        )


class Summary(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        if player.group.treatment == ('exoNo' or 'exoYes'):
            player.final_payoff = player.in_round(C.VOTE_ROUND-1).cum_payoff_game1 + player.in_round(player.round_number).cum_payoff_game2
        else:
            player.final_payoff = player.in_round(C.VOTE_ROUND - 1).cum_payoff_game1 + player.in_round(
                player.round_number).cum_payoff_game2 - player.in_round(C.VOTE_ROUND).additional_vote_share*C.COST_VOTING
        return dict(
            before_vote_round=round(C.VOTE_ROUND-1),
            cum_payoff_game1=player.in_round(C.VOTE_ROUND-1).cum_payoff_game1,
            cum_payoff_game2=player.in_round(player.round_number).cum_payoff_game2,
            player_all_game1_rounds=player.in_rounds(1,round(C.VOTE_ROUND-1)),
            player_game2_rounds=player.in_rounds(C.VOTE_ROUND, player.round_number),
            treatment=player.group.treatment,
            final_payoff=player.final_payoff,
            additional_shares=player.in_round(C.VOTE_ROUND).additional_vote_share,
            additional_costs=player.in_round(C.VOTE_ROUND).additional_vote_share*C.COST_VOTING,
        )



page_sequence = [Introduction, Game1Instructions, MatchInPairsWaitPage, Decision,
                 VoteForGame2Instructions, Vote, VoteWaitPage, VoteResult, Game2Instructions, DecisionAfterVote, ResultsWaitPage, Results, Summary
                 ]



