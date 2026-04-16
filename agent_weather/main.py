import os
from services.agent import Agent


class Main:
    def __init__(self):
        self.agent = Agent()

    def main(self):
        self.agent.run()


if __name__ == "__main__":
    main = Main()
    main.main()