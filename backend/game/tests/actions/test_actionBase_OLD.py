# from game.actions.common import ActionCost
# import pytest

# def test_validator():
#     ActionCost(
#         allowedDice=["die-hory"],
#         requiredDots=10,
#         resources={}
#     )

#     with pytest.raises(ValueError):
#         ActionCost(
#             allowedDice=["die-h"],
#             requiredDots=10,
#             resources={})

#     with pytest.raises(ValueError):
#         ActionCost(
#             allowedDice=["die-hory"],
#             requiredDots=0,
#             resources={})

#     with pytest.raises(ValueError):
#         ActionCost(
#             requiredDots=10,
#             resources={})
