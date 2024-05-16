import tkinter as tk
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import subprocess


def call_cpp_program(arg):
    try:
        result = subprocess.run(['./Kursach/cmake-build-debug/Kursach.exe', arg], stdout=subprocess.PIPE, check=True)
        output_text = result.stdout.decode('utf-8')
        return output_text.split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error calling C++ program: {e}")
        return []


def read_satellite_data(output_lines):
    satellite_data = {}
    satellite_name = None
    for line in output_lines:
        if line.startswith('Name:'):
            satellite_name = line.split(':')[1].strip()
            satellite_data[satellite_name] = {'Trajectory': []}
        elif satellite_name:
            if line.startswith('Position in  ECI'):
                eci_position = line.split(':')[1].strip().strip('{}').split(',')
                satellite_data[satellite_name]['ECI'] = [float(coord.strip()) for coord in eci_position]
            elif line.startswith('Position in ECEF'):
                ecef_position = line.split(':')[1].strip().strip('{}').split(',')
                satellite_data[satellite_name]['ECEF'] = [float(coord.strip()) for coord in ecef_position]
            elif line.startswith('Position in LLA'):
                lla_position = line.split(':')[1].strip().strip('{}').split(',')
                satellite_data[satellite_name]['LLA'] = [float(coord.strip()) for coord in lla_position]
            elif line.startswith('Trajectory in LLA'):
                lla_position = line.split(':')[1].strip().strip('{}').split(',')
                lla_coords = [float(coord.strip()) for coord in lla_position]
                satellite_data[satellite_name]['Trajectory'].append(lla_coords)
            elif line.startswith('Distance to the ground'):
                distance_to_ground = float(line.split(':')[1].strip().split()[0])
                satellite_data[satellite_name]['Distance to the ground'] = distance_to_ground
            elif line.startswith('Distance to MIEM'):
                distance_to_miem = float(line.split(':')[1].strip().split()[0])
                satellite_data[satellite_name]['Distance to MIEM'] = distance_to_miem
    return satellite_data


def plot_satellite_location(satellite_data, satellite_name):
    plt.figure(figsize=(10, 8), facecolor='black')
    ax = plt.axes(projection=ccrs.Orthographic(central_longitude=satellite_data[satellite_name]['LLA'][1],
                                               central_latitude=satellite_data[satellite_name]['LLA'][0]))

    # Добавление Blue Marble изображения в качестве фона
    ax.stock_img()

    img = plt.imread('bluemarble.png')
    img_extent = (-180, 180, -90, 90)
    ax.imshow(img, origin='upper', extent=img_extent, transform=ccrs.PlateCarree())

    lla_position = satellite_data[satellite_name]['LLA']
    lon, lat = lla_position[1], lla_position[0]
    ax.plot(lon, lat, 'ro', transform=ccrs.Geodetic(), label='Satellite Location')

    if 'Trajectory' in satellite_data[satellite_name]:
        trajectory = satellite_data[satellite_name]['Trajectory']
        lons = [pos[1] for pos in trajectory]
        lats = [pos[0] for pos in trajectory]
        ax.plot(lons, lats, 'r', transform=ccrs.Geodetic())

    plt.title(f'Satellite Location: {satellite_name}', color='white')
    plt.show()


def update_satellite_location():
    global satellite_data
    global satellite_name
    output_lines = call_cpp_program("listAll")
    satellite_data = read_satellite_data(output_lines)
    if satellite_name:
        plot_satellite_location(satellite_data, satellite_name)
    root.after(1000, update_satellite_location)


def on_option_change(*args):
    global satellite_name
    satellite_name = selected_option.get()
    if satellite_name and satellite_name in satellite_data:
        plot_satellite_location(satellite_data, satellite_name)


def update_satellite_data():
    call_cpp_program("update list")


def main():
    global satellite_data
    global root
    global satellite_name
    global selected_option

    root = tk.Tk()
    root.title('Satellite Location Viewer')
    root.geometry('300x200')

    label = tk.Label(root, text='Select Satellite:')
    label.pack()

    satellite_names = list(satellite_data.keys())

    if not satellite_names:
        label_no_data = tk.Label(root, text='No satellite data available.')
        label_no_data.pack()
        return

    selected_option = tk.StringVar(root)
    selected_option.set(satellite_names[0])  # Задание значения по умолчанию

    option_menu = tk.OptionMenu(root, selected_option, *satellite_names)
    option_menu.pack()

    selected_option.trace('w', on_option_change)

    update_button = tk.Button(root, text='Update satellite data', command=update_satellite_data)
    update_button.pack()

    update_satellite_location()
    root.mainloop()


if __name__ == "__main__":
    output_lines = call_cpp_program("listAll")
    print(output_lines)
    satellite_data = read_satellite_data(output_lines)
    satellite_name = None
    main()
