import math
import sys
class AOD:
    """class to AOD array."""
    def __init__(self, aod_spec: dict):
        self.idx = -1
        self.site_seperation = 0
        self.n_r = 0
        self.n_c = 0
        if "id" in aod_spec:
            self.idx = aod_spec["id"]
        else:
            raise ValueError(f'AOD id is missed in architecture spec')
        if "site_seperation" in aod_spec:
            self.site_seperation = aod_spec["site_seperation"]
        else:
            raise ValueError(f'AOD site seperation is missed in architecture spec')
        if "r" in aod_spec:
            self.n_r = aod_spec["r"]
        else:
            raise ValueError(f'AOD row number is missed in architecture spec')        
        if "c" in aod_spec:
            self.n_c = aod_spec["c"]
        else:
            raise ValueError(f'AOD column number is missed in architecture spec')        

class SLM:
    """class to SLM array."""
    def __init__(self, slm_spec: dict):
        self.idx = -1
        self.site_seperation = [0, 0]
        self.n_r = 0
        self.n_c = 0
        self.location = None
        self.entanglement_id = -1
        if "id" in slm_spec:
            self.idx = slm_spec["id"]
        else:
            raise ValueError(f'SLM id is missed in architecture spec')
        if "site_seperation" in slm_spec:
            self.site_seperation = slm_spec["site_seperation"]
        else:
            raise ValueError(f'SLM site seperation is missed in architecture spec')
        if "r" in slm_spec:
            self.n_r = slm_spec["r"]
        else:
            raise ValueError(f'SLM row number is missed in architecture spec')        
        if "c" in slm_spec:
            self.n_c = slm_spec["c"]
        else:
            raise ValueError(f'SLM column number is missed in architecture spec')        
        if "location" in slm_spec:
            self.location = slm_spec["location"]
        else:
            raise ValueError(f'SLM location is missed in architecture spec')        


class Architecture:
    """class to define zone architecture."""
    def __init__(self, architecture_spec: dict):
        self.name = None
        self.operation_duration = dict()
        self.storage_zone = []
        self.entanglement_zone = []
        self.dict_SLM = dict()
        self.dict_AOD = dict()
        self.time_atom_transfer = 15 # us
        self.time_rydberg = 0.36 # us
        self.time_1qGate = 0.625 # us
        # parse architecture name
        if "name" in architecture_spec:
            self.name = architecture_spec["name"]
        # parse architecture operation duration
        if "operation_duration" in architecture_spec:
            if "rydberg" in architecture_spec["operation_duration"]:
                self.operation_duration["rydberg"] = architecture_spec["operation_duration"]["rydberg"]
                self.time_rydberg = architecture_spec["operation_duration"]["rydberg"]
            if "atom_transfer" in architecture_spec["operation_duration"]:
                self.operation_duration["atom_transfer"] = architecture_spec["operation_duration"]["atom_transfer"]
                self.time_atom_transfer = architecture_spec["operation_duration"]["atom_transfer"]
            if "1qGate" in architecture_spec["operation_duration"]:
                self.operation_duration["1qGate"] = architecture_spec["operation_duration"]["1qGate"]
                self.time_1qGate = architecture_spec["operation_duration"]["1qGate"]

        # parse architecture zone information
        self.arch_range = architecture_spec["arch_range"]
        self.rydberg_range = architecture_spec["rydberg_range"]
        if "storage_zones" in architecture_spec:
            for zone in architecture_spec["storage_zones"]:
                for slm_spec in zone["slms"]:
                    slm = SLM(slm_spec)
                    self.dict_SLM[slm.idx] = slm
                    self.storage_zone.append(slm.idx)
        if "entanglement_zones" in architecture_spec:
            y_slm = dict()
            for zone in architecture_spec["entanglement_zones"]:
                for slm_spec in zone["slms"]:
                    slm = SLM(slm_spec)
                    self.dict_SLM[slm.idx] = slm
                    if slm.location[1] in y_slm:
                        self.entanglement_zone[y_slm[slm.location[1]]].append(slm.idx)
                    else:
                        y_slm[slm.location[1]] = len(self.entanglement_zone)
                        self.entanglement_zone.append([slm.idx])
                    slm.entanglement_id = zone["zone_id"]
        else:
            raise ValueError(f'entanglement zone configuration is missed in architecture spec')
        
        # parse AOD information
        if "aods" in architecture_spec:
            for aod_spec in architecture_spec["aods"]:
                    aod = AOD(aod_spec)
                    self.dict_AOD[aod.idx] = aod
        else:
            raise ValueError(f'AOD is missed in architecture spec')
    
    def is_valid_SLM(self, idx):
        return (idx in self.dict_SLM)

    def is_valid_SLM_position(self, idx, r, c):
        return r < self.dict_SLM[idx].n_r and c < self.dict_SLM[idx].n_c and r >= 0 and c >= 0

    def is_valid_AOD(self, idx):
        return (idx in self.dict_AOD)
    
    def exact_SLM_location(self, idx, r, c):
        slm = self.dict_SLM[idx]
        assert(self.is_valid_SLM_position(idx, r, c))
        x = slm.site_seperation[0] * c + slm.location[0]
        y = slm.site_seperation[1] * r + slm.location[1]
        return (x, y)

    def exact_SLM_location_tuple(self, loc):
        slm = self.dict_SLM[loc[0]]
        assert(self.is_valid_SLM_position(loc[0], loc[1], loc[2]))
        x = slm.site_seperation[0] * loc[2] + slm.location[0]
        y = slm.site_seperation[1] * loc[1] + slm.location[1]
        return (x, y)


    def preprocessing(self):
        # compute the site region for entanglement zone and the nearest Rydberg site for each storage site
        # we assume we only have one storage zone  or one entanglement zone per row
        # split the row area for SLM sites
        self.entanglement_site_row_space = [] # 2d array. [[y, idx]] => if y' < y, the nearest row to y is the row in zone idx
        self.entanglement_site_col_space = dict()
        # print("self.entanglement_zone")
        # print(self.entanglement_zone)
        y_site = []
        for i, idx in enumerate(self.entanglement_zone):
            slm = self.dict_SLM[idx[0]]
            y_site.append((slm.location[1], i))
        y_site = sorted(y_site, key=lambda site: site[0])
    
        for i in range(len(y_site) - 1):
            slm = self.dict_SLM[self.entanglement_zone[y_site[i][1]][0]]
            low_y = y_site[i][0] + slm.site_seperation[1] * (slm.n_r - 1)
            high_y = y_site[i+1][0]
            self.entanglement_site_row_space.append(((high_y + low_y) / 2, slm.idx))
        self.entanglement_site_row_space.append((sys.maxsize, self.dict_SLM[self.entanglement_zone[y_site[-1][1]][0]].idx))
        # split the column area for SLM sites
        for list_idx in self.entanglement_zone:
            idx = list_idx[0]
            self.entanglement_site_col_space[idx] = []
            slm = self.dict_SLM[idx]
            x = slm.location[0] + slm.site_seperation[0] / 2
            self.entanglement_site_col_space[idx] = [x + c * slm.site_seperation[0] for c in range(slm.n_c - 1)]
            self.entanglement_site_col_space[idx].append(sys.maxsize)
        # print("self.entanglement_site_row_space")
        # print(self.entanglement_site_row_space)
        # print("self.entanglement_site_col_space")
        # print(self.entanglement_site_col_space)
        # compute the nearest Rydberg site for each storage site
        self.storage_site_nearest_Rydberg_site = dict()
        self.storage_site_nearest_Rydberg_site_dis = dict()

        self.Rydberg_site_nearest_storage_site = dict()
        for list_idx in self.entanglement_zone:
            idx = list_idx[0]
            slm = self.dict_SLM[idx]
            self.Rydberg_site_nearest_storage_site[idx] = [[-1 for j in range(slm.n_c)] for i in range(2)]



        for idx in self.storage_zone:
            slm = self.dict_SLM[idx]
            self.storage_site_nearest_Rydberg_site[idx] = [[0 for j in range(slm.n_c)] for i in range(slm.n_r)]
            self.storage_site_nearest_Rydberg_site_dis[idx] = [[0 for j in range(slm.n_c)] for i in range(slm.n_r)]
            x, y = slm.location
            nearest_slm = self.entanglement_site_row_space[-1][1]
            nearest_slm_half_r = self.dict_SLM[nearest_slm].n_r // 2
            next_nearest_slm = -1
            y_lim = self.entanglement_site_row_space[-1][0]
            row_y_l = self.dict_SLM[nearest_slm].location[1]
            row_y = row_y_l + (self.dict_SLM[nearest_slm].n_r - 1) * slm.site_seperation[1]
            if abs(y - row_y_l) < abs(y - row_y):
                row = 0
            else:
                row = self.dict_SLM[nearest_slm].n_r - 1 
            has_increase_y = False
            # find the entanglement slm for the row
            for i in range(len(self.entanglement_site_row_space) - 1):
                if y < self.entanglement_site_row_space[i][0]:
                    nearest_slm = self.entanglement_site_row_space[i][1]
                    next_nearest_slm = self.entanglement_site_row_space[i+1][1]
                    y_lim = self.entanglement_site_row_space[i][0]
                    row = self.dict_SLM[nearest_slm].n_r - 1 
                    has_increase_y = True
                    break
            init_x = x
            init_x_lim = self.entanglement_site_col_space[nearest_slm][-1]
            init_col = self.dict_SLM[nearest_slm].n_c - 1
            for i in range(len(self.entanglement_site_col_space[nearest_slm])):
                if x < self.entanglement_site_col_space[nearest_slm][i]:
                    init_x_lim = self.entanglement_site_col_space[nearest_slm][i]
                    init_col = i
                    break
                
            for r in range(slm.n_r):
                x_lim = init_x_lim
                col = init_col
                x = init_x
                for c in range(slm.n_c):
                    self.storage_site_nearest_Rydberg_site[idx][r][c] = (nearest_slm, row, col)
                    self.storage_site_nearest_Rydberg_site_dis[idx][r][c] = self.distance(idx, r, c, nearest_slm, row, col)
                    
                    if row < nearest_slm_half_r:
                        r_idx = 0
                    else:
                        r_idx = 1
                    if self.Rydberg_site_nearest_storage_site[nearest_slm][r_idx][col] == -1:
                        self.Rydberg_site_nearest_storage_site[nearest_slm][r_idx][col] = (idx, r, c)
                    else:
                        (prev_idx, prev_r, prev_c) = self.Rydberg_site_nearest_storage_site[nearest_slm][r_idx][col]
                        prev_dis = self.storage_site_nearest_Rydberg_site_dis[prev_idx][prev_r][prev_c]
                        if prev_dis > self.storage_site_nearest_Rydberg_site_dis[idx][r][c]:
                            self.Rydberg_site_nearest_storage_site[nearest_slm][r_idx][col] = (idx, r, c)

                    x += slm.site_seperation[0]
                    if x > x_lim and col + 1 < self.dict_SLM[nearest_slm].n_c:
                        col += 1
                        x_lim = self.entanglement_site_col_space[nearest_slm][col]
                y += slm.site_seperation[1]
                if has_increase_y and y > y_lim and next_nearest_slm > -1:
                    has_increase_y = False
                    nearest_slm = next_nearest_slm
                    row = 0   
        
        for key in self.Rydberg_site_nearest_storage_site:
            # check if row_0 is all -1:
            idx_first_none_empty = [-1, -1]
            idx_last_none_empty = [-1, -1]
            for i, row in enumerate(self.Rydberg_site_nearest_storage_site[key]):
                for j, site in enumerate(row):
                    if site != -1:
                        if idx_first_none_empty[i] == -1:
                            idx_first_none_empty[i] = j
                        idx_last_none_empty[i] = j
            # assume at least one row is non empty
            if idx_first_none_empty[0] == -1 and idx_last_none_empty[0] == -1\
                and idx_first_none_empty[1] == -1 and idx_last_none_empty[1] == -1:
                assert(0)
            for i in range(len(self.Rydberg_site_nearest_storage_site[key])):
                if idx_first_none_empty[i] != -1:
                    for j in range(idx_first_none_empty[i] - 1, -1, -1):
                        self.Rydberg_site_nearest_storage_site[key][i][j] = self.Rydberg_site_nearest_storage_site[key][i][idx_first_none_empty[i]]
                if idx_last_none_empty[i] != -1:
                    for j in range(idx_last_none_empty[i] + 1, len(self.Rydberg_site_nearest_storage_site[key][i])):
                        self.Rydberg_site_nearest_storage_site[key][i][j] = self.Rydberg_site_nearest_storage_site[key][i][idx_last_none_empty[i]]
            if idx_first_none_empty[0] == -1 and idx_last_none_empty[0] == -1:
                self.Rydberg_site_nearest_storage_site[key][0] = self.Rydberg_site_nearest_storage_site[key][1]
            elif idx_first_none_empty[1] == -1 and idx_last_none_empty[1] == -1:
                self.Rydberg_site_nearest_storage_site[key][1] = self.Rydberg_site_nearest_storage_site[key][0] 

        # print("self.storage_site_nearest_Rydberg_site")               
        # for key in self.storage_site_nearest_Rydberg_site:
        #     print(key)
        #     for site in self.storage_site_nearest_Rydberg_site[key]:
        #         print(site)
        # print("self.storage_site_nearest_Rydberg_site_dis")
        # print(self.storage_site_nearest_Rydberg_site_dis)
        # print("self.Rydberg_site_nearest_storage_site")
        # print(self.Rydberg_site_nearest_storage_site)
    
    def distance(self, idx1, r1, c1, idx2, r2, c2):
        p1 = self.exact_SLM_location(idx1, r1, c1)
        p2 = self.exact_SLM_location(idx2, r2, c2)
        return math.dist(p1, p2) # Euclidean distance    
    
    def nearest_storage_site(self, idx, r, c):
        slm = self.dict_SLM[idx]
        slm_idx = self.entanglement_zone[slm.entanglement_id][0]
        slm = self.dict_SLM[slm_idx]
        nearest_slm_half_r = slm.n_r // 2
        if r < nearest_slm_half_r:
            return self.Rydberg_site_nearest_storage_site[slm_idx][0][c]
        else:
            return self.Rydberg_site_nearest_storage_site[slm_idx][1][c]

    def nearest_entanglement_site(self, idx, r, c):
        # return the nearest Rydberg site for a qubit in the storage zone
        return self.storage_site_nearest_Rydberg_site[idx][r][c]

    def nearest_entanglement_site_distance(self, idx, r, c):
        # return the distance nearest Rydberg site for a qubit in the storage zone
        return self.storage_site_nearest_Rydberg_site_dis[idx][r][c]

    def nearest_entanglement_site(self, idx1, r1, c1, idx2, r2, c2):
        # return the nearest Rydberg site for two qubit in the storage zone
        # based on the position of two qubits
        storage_site1 = self.exact_SLM_location(idx1, r1, c1)
        storage_site2 = self.exact_SLM_location(idx2, r2, c2)
        site1 = self.storage_site_nearest_Rydberg_site[idx1][r1][c1]
        site2 = self.storage_site_nearest_Rydberg_site[idx2][r2][c2]
        # the nearest zone for both qubits are in the same entanglement zone
        if site1 == site2:
            return [site1]
        elif site1[0] == site2[0]:
            near_x = (storage_site1[0] + storage_site1[1]) // 2
            middle_site_c = (site1[2] + site2[2])// 2
            middle_site_x = self.exact_SLM_location(site1[0], site1[1], middle_site_c)[0]
            near_site_idx = middle_site_c
            # near_site_dis = abs(middle_site_x - near_x)
            # slm = self.dict_SLM[site1[0]]
            # next_dis = abs(middle_site_x + slm.seperation[0] - near_x)
            # if near_site_idx < slm.n_c - 1 and next_dis < near_site_dis:
            #     near_site_idx += 1
            # elif near_site_idx > 0:
            #     next_dis = abs(middle_site_x - slm.seperation[0] - near_x)
            #     if next_dis < near_site_dis:
            #         near_site_idx -= 1

            return [(site1[0], site1[1], near_site_idx)]
        else:
            return [site1, site2]
            slm1 = self.dict_SLM[site1[0]]
            slm2 = self.dict_SLM[site2[0]]
            row_y_1 = slm1.location[1] + site1[1] * slm1.site_seperation[1]
            row_y_2 = slm2.location[1] + site2[1] * slm2.site_seperation[1]
            diff_y_1 = abs(row_y_1 - storage_site1[1]) + abs(row_y_1 - storage_site2[1])
            diff_y_2 = abs(row_y_2 - storage_site1[1]) + abs(row_y_2 - storage_site2[1])
            if diff_y_1 < diff_y_2:
                return (site1[0], site1[1], (site1[2] + site2[2])// 2)
            else:
                return (site2[0], site2[1], (site1[2] + site2[2])// 2)

    def nearest_entanglement_site_dis(self, idx1, r1, c1, idx2, r2, c2):
        # return the sum of the distance to move two qubits to one rydberg site
        storage_site1 = self.exact_SLM_location(idx1, r1, c1)
        storage_site2 = self.exact_SLM_location(idx2, r2, c2)
        list_site = self.nearest_entanglement_site(idx1, r1, c1, idx2, r2, c2)
        dis = sys.maxsize
        for site in list_site:
            exact_site = self.exact_SLM_location(site[0], site[1], site[2])
            # return math.dist(storage_site1, exact_site) + math.dist(storage_site2, exact_site)
            if r1 == r2 and idx1 == idx2:
                dis = min(max(math.dist(storage_site1, exact_site), math.dist(storage_site2, exact_site)), dis)
            else:
                dis = min( math.dist(storage_site1, exact_site) + math.dist(storage_site2, exact_site), dis )
        return dis
    

    def movement_duration(self, x1, y1, x2, y2):
        # d /t^2 = a = 2750m/s
        a = 0.00275
        d = math.dist((x1, y1), (x2, y2))
        # d= 15
        t = math.sqrt(d/a)
        return t

            
            
            

