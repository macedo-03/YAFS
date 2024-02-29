import os


class myConfig:

    def __init__(self):

        self.graphicTerminal = True
        self.verbose_log = False
        self.myConfiguration = 'small'
        self.resultFolder = 'data'
        self.num_windows = 10
        self.win_time = 10000
        self.popSize = 100
        self.nGen = 400

        try:
            os.stat(self.resultFolder)
        except:
            os.mkdir(self.resultFolder)