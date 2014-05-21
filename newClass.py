# -*- coding:utf-8 -*-
##############################
##基于社交圈的社交网络朋友推荐算法##
##code by HanJianan##
##2014.05##
##############################




#获取文本行数
def get_line_num(file_name):
    count = -1
    for count, line in enumerate(open(file_name, 'rU')):
        pass
    count += 1
    return count


#全局网络类    
class SocialNetwork(object):

    #初始化
    def __init__(self,file_name,node_num):
        self.file_name=file_name  #数据文件名
        self.node_num=int(node_num)  #网络结点个数
        self.line_num=get_line_num(file_name)  #网络边个数
        self.list_map=self.get_map()  #网络边邻接表



    def get_map(self):
    	list_map=[[]for i in range(self.node_num)]
    	self.current_file=open(self.file_name)
    	for i in range(self.line_num):              
            now_line=self.current_file.readline()
            words=now_line.split()
            if len(words)!=0 :
                start=int(words.pop(0))
                end=int(words.pop(0))
                if  end not in list_map[start]:
                    list_map[start].append(end)
                    list_map[end].append(start)
        self.current_file.close()
        return list_map



#用户自我网络类
class UserNetwork(object):

    def __init__(self,uid,list_map):
        self.node_list=[uid] #自我网络中的结点
        self.network=self.get_self_network(list_map) #用户自我网络
        self.edge_similarity_dict={}   #自我网络相邻边相似度字典
        self.average_edge_similarity=self.get_average_edge_similarity() #计算平均邻边相似度
        self.ncc_dict={}     #自我网络边聚集系数字典
        self.average_ncc=self.get_average_ncc()   #计算平均边聚集系数

        
    #获取用户自我网络
    def get_self_network(self,list_map):
        network={}
        for now_node in self.node_list:
            node_edge=[]
            for node in list_map[now_node]:
                node_edge.append(node)
                if node not in self.node_list:
                    self.node_list.append(node)
            network[now_node]=node_edge
        return network



    #获取网络中所有相邻边的平均相似度
    def get_average_edge_similarity(self):
        pair_num=0
        all_similarity=0
        searched_nodes=[]
        for s in self.node_list:
            self.edge_similarity_dict[s]={}
            for e1 in self.network[s]:
                for e2 in self.network[s]:
                    if self.edge_similarity_dict[s].has_key((e1,e2))==False:
                        edge_pair=EdgePair(s,e1,e2)
                        this_similarity=edge_pair.get_similarity(self.network)
                        pair_num+=1
                        self.edge_similarity_dict[s][(e1,e2)]=this_similarity
                        self.edge_similarity_dict[s][(e2,e1)]=this_similarity
                        all_similarity+=this_similarity
        return float(all_similarity)/float(pair_num)
     

    #获取所有边的平均边聚集系数
    def get_average_ncc(self):
        edge_num=0
        all_ncc=0
        for s in self.node_list:
            for e in self.network[s]:
                if self.ncc_dict.has_key((s,e))==False:
                    edge=Edge(s,e)
                    now_ncc=edge.get_ncc(self.network)
                    self.ncc_dict[(s,e)]=now_ncc
                    self.ncc_dict[(e,s)]=now_ncc
                    all_ncc+=now_ncc
                    edge_num+=1
        return float(all_ncc)/float(edge_num)






#用户结点类
class User(object):
    
    def __init__(self,uid,net):
        self.uid=uid     #用户id
        self.net=net  #用户所属关系网络
        self.network=net.network
        self.circles=[]    #用户的朋友圈
        self.friend_max_circle={}  #潜在朋友的最大可能性圈子
        self.node_similarity_list=[0 for i in range(len(net.node_list))]  #用户与周围朋友相似性list
    

    #基于关系的社交圈检测算法    
    def get_circle(self,sv,ncc): #参数：用户user,相似性阈值sv,边聚集系数ncc
        social_circle=[]    #初始化社交圈集合
        #计算社交圈
        searched_edges=[] #存储已知社团中的边
        for ei in self.network[self.uid]:
            if ei not in searched_edges:
                searched_edges.append(ei)
                edge_circle=[] #edge_circle存储当前正在检测的社团中的边
                edge_circle.append(ei)                
                #检测ei的社交圈
                for ej in edge_circle:
                    for ek in self.network[self.uid]:
                        if ek not in searched_edges and self.net.edge_similarity_dict[self.uid][(ei,ek)]>sv:
                            edge_circle.append(ek)
                            searched_edges.append(ek)
                #判断是不是噪音
                flag=False 
                if len(edge_circle)<4:
                    flag=True
                    for s in edge_circle:
                        for e in self.network[s]:
                            if self.net.ncc_dict[(s,e)]>=ncc:
                                flag=False
                                break
                        if flag==False:
                            break
                if flag==False:
                    social_circle.append(edge_circle)
        self.circles=social_circle
        return social_circle


    #寻找与用户有公共邻居但无边相连的顶点
    def get_candidate(self):
        candidate=[]
        for s in self.network[self.uid]:
            for e in self.network[s]:
                if e not in self.network[self.uid] and e not in candidate and e!=self.uid:
                    candidate.append(e)
        self.candidate=candidate
        return candidate
     

    #用户和用户的相似度定义
    def get_similarity(self,target):
        max_circle=[]
        max_overlap=0
        similarity=0
        for c1 in self.circles:
            nc1=Circle(self.uid,c1)
            for c2 in target.circles:
                nc2=Circle(target.uid,c2)
                now_overlap=nc1.get_overlap(nc2,self.network)
                similarity+=now_overlap
                if now_overlap>max_overlap:
                    max_circle=nc1.member
        self.friend_max_circle[target.uid]=max_circle
        uno=self.net.node_list.index(target.uid)
        self.node_similarity_list[uno]=similarity            
        return similarity

    #推荐好友
    def recommend(self,k,sv,ncc):
        candidate=self.get_candidate()
        for node in candidate:
            now_node=User(node,self.net)
            now_node.get_circle(sv,ncc)
            self.get_similarity(now_node)
        protential_firends=[]
        for i in range(k):
            uno=self.node_similarity_list.index(max(self.node_similarity_list))
            uid=self.net.node_list[uno]
            protential_firends.append(uid)
            self.node_similarity_list[uno]=0
        for friend in protential_firends:
            print "The user %d may be user %d's friend"%(friend,self.uid)
            print "He/She maybe belong to user %d's social circle:"%self.uid,self.friend_max_circle[friend]




    
#边类
class Edge(object):

    def __init__(self,start,end):
        self.start=start
        self.end=end

    #获取边聚集系数
    def get_ncc(self,network):
        ki=len(network[self.start])  #计算起点的度
        kj=len(network[self.end])  #计算终点的度        
        #计算相邻公共结点
        z=0
        for i in network[self.start]:
            if i in network[self.end]:
                z+=1
        if min(ki-1,kj-1)!=0:        
            return float(z+1)/float(min(ki-1,kj-1))
        else:
            return 0



#相邻边对类
class EdgePair(object):

    def __init__(self,start,end1,end2):
        self.start=start
        self.end1=end1
        self.end2=end2

    #相邻边相似度函数        
    def get_similarity(self,network):
        all_node=len(network[self.end1])+len(network[self.end2])
        same_node=0
        for node in network[self.end1]:
                if  node in network[self.end2]:
                    same_node+=1
        return float(same_node)/float(all_node)




#社交圈类
class Circle(object):

    def __init__(self,uid,member):
        self.member=member
        self.user=user

    #重叠度定义
    def get_overlap(self,target,network):
        searched_nodes=[]
        n=0
        m=0
        for k in self.member:
            if k not in searched_nodes:
                if k in target.member:
                    n+=1
                    searched_nodes.append(k)
                    for l in network[k]:
                        if l not in searched_nodes and l in self.member and l in target.member :
                            m+=1
        return n*(m+1)




#print "input file name please"
file_name='0.edges'#raw_input("> ")
#print "input node number in the map please"
node_num=4050#raw_input("> ")
#print "input user  please"
uid=1#raw_input("> ")
#print "input the number of the friends you want to recommmend"
friend_num=3
#测试数据
all_node=SocialNetwork(file_name, node_num)
net=UserNetwork(uid,all_node.list_map)
sv=net.average_edge_similarity
ncc=net.average_ncc
user=User(uid,net)
user.get_circle(sv,ncc)
circle_num=1
for circle in user.circles:
    print "this is circle %d:"%circle_num,circle
    circle_num+=1
user.get_candidate()    
user.recommend(friend_num,sv,ncc)    
    
                
