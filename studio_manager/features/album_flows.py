"""Album management flows"""
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_confirmation
from .project_tracker import AlbumManager
from ..utils.helpers import Path

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
    manager = AlbumManager(album_path)
    manager.list_songs()
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Add songs")
    console.print("  2 - Remove song")
    console.print("  3 - Reorder songs")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        add_songs_to_album_flow(album_path)
    elif choice == "2":
        if manager.data["songs"]:
            idx = int(input(f"Select song to remove (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= idx < len(manager.data["songs"]):
                manager.remove_song(Path(manager.data["songs"][idx]["path"]))
    elif choice == "3":
        if manager.data["songs"]:
            manager.list_songs()
            song_idx = int(input(f"Select song to move (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= song_idx < len(manager.data["songs"]):
                new_pos = int(input("New position: "))
                song_path = Path(manager.data["songs"][song_idx]["path"])
                manager.reorder_song(song_path, new_pos)
                manager.list_songs()

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
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Create new album")
    console.print("  2 - Manage existing album")
    console.print("  3 - View unassigned songs")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        artist = input("Artist name: ").strip()
        album_name = input("Album name: ").strip()
        
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
    elif choice == "2" and albums:
        idx = int(input(f"Select album (1-{len(albums)}): ")) - 1
        if 0 <= idx < len(albums):
            manage_album_flow(albums[idx])
        input("\nPress Enter to continue...")
    elif choice == "3":
        view_unassigned_songs_flow()