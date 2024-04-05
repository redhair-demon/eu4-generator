import random

con = 'bcdfghjklmnpqrstvwxz'
con_f = [1.49, 2.78, 4.25, 2.23, 2.02, 6.09, 0.15, 0.77, 4.03, 2.41, 6.75, 1.93, 0.1, 5.99, 6.33, 9.06, 0.98, 2.36, 0.15, 0.07]
vow = 'aeiouy'
vow_f = [8.17, 12.7, 6.97, 7.51, 2.76, 1.97]

def generate_names(n):
    file_word = []
    with open('english-nouns.txt', 'r') as file:
        for line in file:
            line = line.replace("\n", "")
            if len(line) > 4:
                file_word.append(line)
    # print(len(file_word))
    result = set()
    while len(result) < n:
        result.update(gener(file_word, min(n, len(file_word))))
    return list(result)[:n]

def gener(file_word, n):
    base_word = random.sample(file_word, k=n)
    # base_word = random.sample(list(filter(lambda a: len(a)>4 and len(a)<11,words.words())), k=n)
    
    base_word = [x.lower() for x in base_word]
    for i, w in enumerate(base_word):
        reps = random.sample(list(range(len(w))), k=random.randint(3, len(w)-1))
        # print(w, reps)
        for r in reps:
            if base_word[i][r] in con:
                temp = con_f.copy()
                temp.pop(con.index(base_word[i][r]))
                base_word[i] = base_word[i][:r] + random.choices(con.replace(base_word[i][r], ""), temp)[0] + base_word[i][r+1:]
            else:
                temp = vow_f.copy()
                temp.pop(vow.index(base_word[i][r]))
                base_word[i] = base_word[i][:r] + random.choices(vow.replace(base_word[i][r], ""), temp)[0] + base_word[i][r+1:]
                # base_word[i] = base_word[i][:r] + random.choices(typ(base_word[i][r]).replace(base_word[i][r], ""), ) + base_word[i][r+1:]
        # print(base_word[i])
    return [x[:11] for x in base_word]
