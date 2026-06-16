"""Album management flows"""
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_confirmation, get_input_with_completion, get_text_input, get_choice
from .project_tracker import AlbumManager
from ..data.history import ProjectHistory

# Global history reference for name suggestions
_history = None

def set_album_history(history_obj: ProjectHistory):
    """Set the history object for name suggestions in album flows"""
    global _history
    _history = history_obj

def add_songs_to_album_flow(album_path: Path):
    """Add songs to an album"""
    manager = AlbumManager(album_path)
    unassigned = manager.get_unassigned_songs(Path.cwd())
    
    if not unassigned:
        print_info("No unassigned songs found")
        return
    
    console.print("\n[bold]Unassigned Songs:[/bold]")
    for i, song in enumerate(unassigned, 1):
        console.print(f"  [cyan]{i}[/cyan] - {song.parent.name}/{song.name}")
    
    choice = input("\nSelect song to add (or 'a' to add all, 'b' to go back): ").strip()
    
    if choice.lower() == 'a':
        for song in unassigned:
            manager.add_song(song)
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(unassigned):
            position = input(f"Position in album (1-{len(manager.data['songs']) + 1}, Enter for end): ").strip()
            pos = int(position) if position.isdigit() else None
            manager.add_song(unassigned[idx], pos)
    
    manager.list_songs()

def manage_album_flow(album_path: Path):
    """Manage an existing album"""
    clear_screen()
    manager = AlbumManager(album_path)
    
    console.print(Panel.fit(f"[bold white]Manage Album: {manager.data['name']}[/bold white]", style="white"))
    
    manager.list_songs()
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Add songs")
    console.print("  2 - Remove song")
    console.print("  3 - Reorder songs")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        add_songs_to_album_flow(album_path)
        manage_album_flow(album_path)
        return
    elif choice == "2":
        if manager.data["songs"]:
            idx = int(input(f"Select song to remove (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= idx < len(manager.data["songs"]):
                manager.remove_song(Path(manager.data["songs"][idx]["path"]))
                manage_album_flow(album_path)
                return
        else:
            print_warning("No songs in this album")
            input("\nPress Enter to continue...")
            manage_album_flow(album_path)
            return
    elif choice == "3":
        if manager.data["songs"]:
            manager.list_songs()
            song_idx = int(input(f"Select song to move (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= song_idx < len(manager.data["songs"]):
                new_pos = int(input("New position: "))
                song_path = Path(manager.data["songs"][song_idx]["path"])
                manager.reorder_song(song_path, new_pos)
                manage_album_flow(album_path)
                return
        else:
            print_warning("No songs in this album")
            input("\nPress Enter to continue...")
            manage_album_flow(album_path)
            return
    elif choice == 'b':
        return
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        manage_album_flow(album_path)
        return

def view_unassigned_songs_flow():
    """View all songs not assigned to an album"""
    clear_screen()
    console.print(Panel.fit("[bold white]Unassigned Songs[/bold white]", style="white"))
    
    manager = AlbumManager(Path.cwd())
    unassigned = manager.get_unassigned_songs(Path.cwd())
    
    if not unassigned:
        print_info("All songs are assigned to albums")
    else:
        table = Table(title="Songs Not in Any Album", style="white")
        table.add_column("Artist", style="cyan")
        table.add_column("Song Name", style="green")
        table.add_column("Path", style="dim")
        
        for song in unassigned:
            table.add_row(song.parent.name, song.name, str(song))
        
        console.print(table)
    
    input("\nPress Enter to continue...")

def search_albums_flow():
    """Search for albums by name, artist, or track count"""
    clear_screen()
    console.print(Panel.fit("[bold white]Search Albums[/bold white]", style="white"))
    
    albums_path = Path.cwd() / "artists"
    all_albums = []
    
    if albums_path.exists():
        for artist_dir in albums_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir() and (project_dir / ".album.json").exists():
                        manager = AlbumManager(project_dir)
                        all_albums.append({
                            "path": project_dir,
                            "name": manager.data["name"],
                            "artist": project_dir.parent.name,
                            "tracks": manager.data["total_tracks"],
                            "status": manager.data.get("status", "in_progress")
                        })
    
    if not all_albums:
        print_info("No albums found")
        input("\nPress Enter to continue...")
        return
    
    console.print("\n[bold]Search by:[/bold]")
    console.print("  [cyan]1[/cyan] - Album name")
    console.print("  [cyan]2[/cyan] - Artist name")
    console.print("  [cyan]3[/cyan] - Track count (e.g., >5)")
    console.print("  [cyan]4[/cyan] - Show all albums")
    console.print("  [cyan]b[/cyan] - Go back")
    
    search_type = input("\nSelect option: ").strip()
    
    if search_type == 'b':
        return
    elif search_type == "1":
        search_term = input("Enter album name (or partial name): ").strip().lower()
        results = [a for a in all_albums if search_term in a["name"].lower()]
    elif search_type == "2":
        search_term = input("Enter artist name (or partial name): ").strip().lower()
        results = [a for a in all_albums if search_term in a["artist"].lower()]
    elif search_type == "3":
        search_term = input("Enter track count (e.g., 5 for exactly 5, >5 for more than 5): ").strip()
        try:
            if search_term.startswith('>'):
                count = int(search_term[1:])
                results = [a for a in all_albums if a["tracks"] > count]
            elif search_term.startswith('<'):
                count = int(search_term[1:])
                results = [a for a in all_albums if a["tracks"] < count]
            else:
                count = int(search_term)
                results = [a for a in all_albums if a["tracks"] == count]
        except ValueError:
            print_error("Invalid search term. Please use a number (e.g., 5, >5, <5)")
            input("\nPress Enter to continue...")
            return
    elif search_type == "4":
        results = all_albums
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        return
    
    if not results:
        print_warning(f"No albums found matching '{search_term}'")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Search Results: {len(results)} albums found", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Album Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Tracks", style="magenta")
    table.add_column("Status", style="dim")
    
    for idx, album in enumerate(results, 1):
        status = album["status"].replace('_', ' ').title()
        table.add_row(str(idx), album["name"], album["artist"], str(album["tracks"]), status)
    
    console.print(table)
    
    if get_confirmation("\nManage an album from the search results?"):
        choice = input("Enter album number to manage: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                manage_album_flow(results[idx]["path"])
                return
            else:
                print_error("Invalid album number")
        else:
            print_error("Please enter a valid number")
        input("\nPress Enter to continue...")

def album_management_flow():
    """Manage albums and song organization"""
    clear_screen()
    console.print(Panel.fit("[bold white]Album Management[/bold white]", style="white"))
    
    albums_path = Path.cwd() / "artists"
    albums = []
    
    if albums_path.exists():
        for artist_dir in albums_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir() and (project_dir / ".album.json").exists():
                        albums.append(project_dir)
    
    if albums:
        console.print("\n[bold]Existing Albums:[/bold]")
        for i, album in enumerate(albums, 1):
            manager = AlbumManager(album)
            console.print(f"  [cyan]{i}[/cyan] - {manager.data['name']} ({manager.data['total_tracks']} tracks)")
    else:
        console.print("[dim]No albums found. Create one with option 1.[/dim]")
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  [cyan]1[/cyan] - Create new album")
    console.print("  [cyan]2[/cyan] - Manage existing album (from list)")
    console.print("  [cyan]3[/cyan] - Search for an album")
    console.print("  [cyan]4[/cyan] - View unassigned songs")
    console.print("  [cyan]b[/cyan] - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        if _history and len(_history.data["artists"]) > 0:
            print_info("\nTip: Press TAB to see available artists from history")
        artist = get_input_with_completion("\nArtist name", "artist", _history, allow_backtrack=False)
        
        if artist == "##BACKTRACK##":
            return
        
        album_name = get_text_input("\nAlbum name", allow_empty=False, allow_backtrack=False)
        if album_name == "##BACKTRACK##":
            return
        
        artist_path = Path.cwd() / "artists" / artist
        album_path = artist_path / album_name
        
        if album_path.exists():
            print_warning("Album already exists")
        else:
            album_path.mkdir(parents=True, exist_ok=True)
            manager = AlbumManager(album_path)
            manager.save()
            print_success(f"Album '{album_name}' created for {artist}")
            
            if get_confirmation("Add songs to this album now?"):
                add_songs_to_album_flow(album_path)
        
        input("\nPress Enter to continue...")
        album_management_flow()
        return
        
    elif choice == "2" and albums:
        if not albums:
            print_warning("No albums to manage")
            input("\nPress Enter to continue...")
            album_management_flow()
            return
        
        idx = input(f"Select album (1-{len(albums)}): ").strip()
        if idx.isdigit():
            idx = int(idx) - 1
            if 0 <= idx < len(albums):
                manage_album_flow(albums[idx])
                album_management_flow()
                return
            else:
                print_error("Invalid album number")
                input("\nPress Enter to continue...")
                album_management_flow()
                return
        else:
            print_error("Please enter a valid number")
            input("\nPress Enter to continue...")
            album_management_flow()
            return
            
    elif choice == "3":
        search_albums_flow()
        album_management_flow()
        return
        
    elif choice == "4":
        view_unassigned_songs_flow()
        album_management_flow()
        return
        
    elif choice == 'b':
        return
    
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        album_management_flow()
        return