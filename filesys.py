import os
import sessions

# create new...

def createNewProject(name, type, artist, daw):
    artist_dir = str(os.getcwd())+"/artists/"+str(artist)+"/"
    project_dir = str(os.getcwd())+"/artists/"+str(artist)+"/"+str(name)+"/"

    if(artistFolderExists(artist_dir)):
        if(projectFolderExists(project_dir)):
            # artist and project folder found
            print("\nFULL PATH FOUND: "+project_dir)
        else:
            # make project folder (artist folder exists, project folder doesn't)
            os.mkdir(project_dir)
            print("\nCreating Project Folder... "+project_dir)
    else:
        # make artist folder (neither exists yet)
        os.mkdir(artist_dir)
        print("\nCreating Artist Folder... "+artist_dir)

        # make project folder (now artist folder exists)
        os.mkdir(project_dir)
        print("\nCreating Project Folder... "+project_dir)
    
    if type == "S":
        sessions.createNewSessionFromTemplate(name, artist, daw)

    elif type == "A":
        # Album only creates a directory for now
        pass

# checking for existing directories

def artistFolderExists(artist_directory):
    if(os.path.exists(artist_directory)):
        return True
    else:
        print("\nERR: ARTIST FOLDER NOT FOUND!")
        return False
    
def projectFolderExists(project_directory):
    if(os.path.exists(project_directory)):
        return True
    else:
        print("\nERR: PROJECT FOLDER NOT FOUND!")
        return False
    
def dawFolderExists(project_directory, daw):
    if(os.path.exists(project_directory+"/"+daw)):
        print("\nERR: DAW FOLDER FOUND!")
        return True
    else:
        return False