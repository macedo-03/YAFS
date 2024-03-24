import os


class myConfig:

    def __init__(self):

        self.graphicTerminal = True
        self.verbose_log = False
        self.myConfiguration = 'medium'
        self.resultFolder = 'data'
        self.num_windows = 1
        self.win_time = 10000
        self.popSize = 100
        self.nGen = 100

        try:
            os.stat(self.resultFolder)
        except:
            os.mkdir(self.resultFolder)