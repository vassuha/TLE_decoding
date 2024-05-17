import tkinter as tk
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import subprocess
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Функция для вызова программы на C++
def call_cpp_program(arg, callback):
    def run_program():
        try:
            result = subprocess.run(['./Kursach/cmake-build-debug/Kursach.exe', arg], stdout=subprocess.PIPE,
                                    check=True)
            output_text = result.stdout.decode('utf-8')
            callback(output_text.split('\n'))
        except subprocess.CalledProcessError as e:
            print(f"Error calling C++ program: {e}")
            callback([])

    threading.Thread(target=run_program).start()


# Функция для чтения данных со спутника
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


# Функция для отображения местоположения спутника
def plot_satellite_location(satellite_data, satellite_name):
    if satellite_name not in satellite_data or 'LLA' not in satellite_data[satellite_name]:
        print(f"Satellite data for {satellite_name} is not available.")
        return

    lla_position = satellite_data[satellite_name]['LLA']
    lon, lat = lla_position[1], lla_position[0]

    fig.clear()
    ax = fig.add_subplot(111, projection=ccrs.Orthographic(central_longitude=lon, central_latitude=lat))
    ax.stock_img()

    img = plt.imread('bluemarble.png')
    img_extent = (-180, 180, -90, 90)
    ax.imshow(img, origin='upper', extent=img_extent, transform=ccrs.PlateCarree())

    ax.plot(lon, lat, 'ro', transform=ccrs.Geodetic(), label='Satellite Location')

    if 'Trajectory' in satellite_data[satellite_name]:
        trajectory = satellite_data[satellite_name]['Trajectory']
        lons = [pos[1] for pos in trajectory]
        lats = [pos[0] for pos in trajectory]
        ax.plot(lons, lats, 'r', transform=ccrs.Geodetic())

    ax.set_title(f'{satellite_name}', color='white')
    canvas.draw()


# Функция для отображения детальной информации о спутнике
def display_satellite_info(satellite_data, satellite_name):
    if satellite_name not in satellite_data:
        satellite_info_label.config(text=f"Satellite data for {satellite_name} is not available.")
        return

    info = satellite_data[satellite_name]
    info_text = f"{satellite_name}\n"
    if 'LLA' in info:
        info_text += f"Latitude: {info['LLA'][0]}° \nLongitude: {info['LLA'][1]}° \n"
    if 'Distance to the ground' in info:
        info_text += f"Altitude: {info['Distance to the ground']} km\n"
    if 'Distance to MIEM' in info:
        info_text += f"Distance to MIEM: {info['Distance to MIEM']} km\n"

    satellite_info_label.config(text=info_text)


# Функция для обновления местоположения спутника
def update_satellite_location():
    global satellite_data
    global satellite_name

    def on_data_received(output_lines):
        global satellite_data
        satellite_data = read_satellite_data(output_lines)
        if satellite_name:
            plot_satellite_location(satellite_data, satellite_name)
            display_satellite_info(satellite_data, satellite_name)
        root.after(5000, update_satellite_location)  # Schedule next update

    call_cpp_program(category_option.get(), on_data_received)


# Обработчик изменения опции выбора спутника
def on_option_change(*args):
    global satellite_name
    satellite_name = selected_option.get()
    if satellite_name and satellite_name in satellite_data:
        plot_satellite_location(satellite_data, satellite_name)
        display_satellite_info(satellite_data, satellite_name)


# Обработчик изменения категории
def on_category_change(*args):
    global satellite_data
    global selected_option
    global satellite_name
    category = category_option.get()

    def on_data_received(output_lines):
        global satellite_data
        satellite_data = read_satellite_data(output_lines)
        satellite_names = list(satellite_data.keys())
        if satellite_names:
            selected_option.set(satellite_names[0])
            menu = satellite_menu['menu']
            menu.delete(0, 'end')
            for name in satellite_names:
                menu.add_command(label=name, command=tk._setit(selected_option, name))
            satellite_name = satellite_names[0]
            plot_satellite_location(satellite_data, satellite_name)
            display_satellite_info(satellite_data, satellite_name)

    if category:
        call_cpp_program(category, on_data_received)


# Функция для обновления данных спутника
def update_satellite_data():
    category = category_option.get()
    call_cpp_program("update", lambda output_lines: satellite_data.update(read_satellite_data(output_lines)))


# Главная функция
def main():
    global satellite_data
    global root
    global satellite_name
    global selected_option
    global category_option
    global satellite_menu
    global ax
    global canvas
    global fig
    global satellite_info_label

    root = tk.Tk()
    root.title('Satellite Location Viewer')
    root.geometry('1000x600')

    # Используем Frame для размещения виджетов
    top_frame = tk.Frame(root)
    top_frame.pack(side=tk.TOP, fill=tk.X)

    left_frame = tk.Frame(top_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.Y)

    right_frame = tk.Frame(top_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    category_label = tk.Label(left_frame, text='Select Category:')
    category_label.pack()

    categories = ["Space stations", "GOES", "Last 30 days", "IRIDIUM", "R4uab"]
    category_option = tk.StringVar(root)
    category_option.set(categories[0])

    category_menu = tk.OptionMenu(left_frame, category_option, *categories)
    category_menu.pack()

    category_option.trace('w', on_category_change)

    label = tk.Label(left_frame, text='Select Satellite:')
    label.pack()

    satellite_names = list(satellite_data.keys())
    selected_option = tk.StringVar(root)
    if satellite_names:
        selected_option.set(satellite_names[0])
    else:
        selected_option.set('')

    satellite_menu = tk.OptionMenu(left_frame, selected_option, *satellite_names)
    satellite_menu.pack()

    selected_option.trace('w', on_option_change)

    update_button = tk.Button(left_frame, text='Update satellite data', command=update_satellite_data)
    update_button.pack()

    satellite_info_label = tk.Label(left_frame, text='', justify=tk.LEFT, anchor='w')
    satellite_info_label.pack(fill=tk.BOTH, expand=True)

    fig = plt.figure(figsize=(10, 8), facecolor='black')
    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    update_satellite_location()
    root.mainloop()


if __name__ == "__main__":
    def on_initial_data_received(output_lines):
        global satellite_data
        global satellite_name
        satellite_data = read_satellite_data(output_lines)
        satellite_name = None
        main()


    call_cpp_program("listAll", on_initial_data_received)
