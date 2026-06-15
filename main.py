import filesys

def main():
    objective = input("""
1. new project
2. open project
3. pull up current tasks

""").strip()

    while(objective != "1" and 
    objective != "2" and 
    objective != "3"):
    
        objective = input("""
Invalid input. Please try again.
1. new project
2. open project
3. pull up current tasks

""").strip()
    
    objective = int(objective)

    if objective is 1:

        # engineer
        num_engineers = input("\nEnter the number of engineers on this session: ")
        while(not num_engineers.isnumeric() or 
              int(num_engineers) > 20 or
              int(num_engineers) < 0):
            print("\nERR: Invalid input. Try again.")
            num_engineers = input("\nEnter the number of engineers on this session: ")

        num_engineers = int(num_engineers)
        engineers = [0] * num_engineers
        
        if num_engineers is 1:
            engineers[0] = input("\nEnter the name of the engineer of this session: ").strip().lower()
        elif num_engineers > 1:
            i = 0
            for name in engineers:
                engineers[i] = input("\nEnter the name of engineer #"+str(i+1)+": ").strip().lower()
                i+=1
        
        # project name
        name = input("\nEnter the name of your project: ")
        
        # song or album
        type = input("\nEnter S for Song, or A for Album: ").strip().upper()
        while(type != "S" and type != "A"):
            type = input("\nInvalid entry. Enter S for Song, or A for Album: ").strip().upper()
        
        # artist name
        artist = input("\nEnter the name of the artist: ").strip().lower()

        if(type == "S"):
            # daw selection for song 
            daw = input("\nEnter the daw you're using. Enter P for Pro Tools, A for Ableton, and L for Logic: ").strip().upper()
            while(daw != "P" and daw != "A" and daw != "L"):
                daw = input("\nEnter the daw you're using. Enter P for Pro Tools, A for Ableton, and L for Logic: ").strip().upper()
        else:
            # leaving daw empty for album option
            daw = ""

        # then, create the project
        filesys.createNewProject(name, type, artist, daw)    
        
    if objective is 2:
        print("Section Not Done")

    if objective is 3:
        print("Section Not Done")

if __name__ == "__main__":
    main()
