from pydantic import BaseModel

class ActionBase:
	teamId: TeamId
	entities: Entities
	state: GameState

	errors: MessageBuilder
	info: MessageBuilder

	def cost() -> ActionCost:
	    raise NotImplementedError("ActionBase is an interface")

	def commit() -> str:
		self.apply()

	def apply() -> None:
		raise NotImplementedError("ActionBae is an interface")