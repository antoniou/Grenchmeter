import sys

class ResourceStatistics:
    def __init__(self,fileName):
        self.stats=[]
        self.file=fileName
        
        #(numMachines,sshOverhead,totalOverhead)
    def addStats(self,statsList):
        self.stats.append(statsList)
        
    def __call__(self):
        file=open(self.file,'w')
        for stat in self.stats:
            for elem in stat:
                file.write(str(elem))
                if stat.index(elem) == len(stat) - 1 :
                    file.write('\n')
                else:
                    file.write('\t')
        file.close()
