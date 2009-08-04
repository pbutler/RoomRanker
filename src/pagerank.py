#!/usr/bin/python
# vim: et ts=4 sw=4 smarttab

def pageRank(links):
    N = len(links)
    L = [0]*N
    d = .85
    for j in range(N):
        L[j] = reduce(lambda x,y:x+y, [links[i][j] for i in range(N)])

    state    = [ 1/float(N) for i in range(N) ]
    newstate = [ 1/float(N) for i in range(N) ]
    print state
    for q in range(20):
        for i in range(N):
            newstate[i] = (1.-d) 
            for j in range(N):
                if i == j: 
                    continue
                if links[i][j] > 0:
                    newstate[i] += d*state[j] / L[j]
        state = newstate
        print state

if __name__ == "__main__":
    links = [ [0, 1,1,1], [ 0,0,0,1], [0,1,0,1], [0,0,0,0]]
    links = [ [0, 0,1,0], [ 1,0,0,0], [1,1,0,1], [0,0,0,0]]
    #links = [ [0, 1,0], [ 0,1,1], [0,1,0]]
    #links = [ [1, 1,1], [ 1,1,1], [1,1,1]]
    pageRank(links)
