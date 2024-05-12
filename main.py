import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import subprocess
import time

def call_cpp_program():
    result = subprocess.run(['./Kursach/cmake-build-debug/Kursach.exe', 'arg1', 'arg2'], stdout=subprocess.PIPE)
    #result = subprocess.run(['./Test_project/cmake-build-debug/Test_project.exe', 'arg1', 'arg2'], stdout=subprocess.PIPE)
    output_text = result.stdout.decode('utf-8')

    # Разбиваем вывод программы на строки
    output_lines = output_text.split('\n')

    # Выводим строки
    print("output")
    for line in output_lines:
        print(line)
    print("end output")
    return output_lines

def read_satellite_data(output_lines):
    # with open(file_path, 'r') as file:
    #     data = file.readlines()
    #     print(data)

    satellite_data = {}
    satellite_name = None
    for line in output_lines:
        if line.startswith('Name:'):
            satellite_name = line.split(':')[1].strip()
            satellite_data[satellite_name] = {}
            print(satellite_name)
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
            elif line.startswith('Distance to the ground'):
                distance_to_ground = float(line.split(':')[1].strip().split()[0])
                satellite_data[satellite_name]['Distance to the ground'] = distance_to_ground
            elif line.startswith('Distance to MIEM'):
                distance_to_miem = float(line.split(':')[1].strip().split()[0])
                satellite_data[satellite_name]['Distance to MIEM'] = distance_to_miem
    return satellite_data


def plot_satellite_location(satellite_data, satellite_name):
    plt.figure(figsize=(10, 8))
    plt.title(f'Satellite Location: {satellite_name}')
    lla_position = satellite_data[satellite_name]['LLA']
    lon, lat = lla_position[1], lla_position[0]
    m = Basemap(projection='ortho', lat_0=lat-10, lon_0=lon-10)
    m.drawcoastlines()

    x, y = m(lon, lat)
    m.plot(x, y, 'ro', label='Satellite Location')
    m.bluemarble()
    # plt.legend()
    plt.show()


def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        return file_path
    else:
        return None


def on_submit():
    global satellite_data
    global entry

    satellite_name = entry.get()
    if satellite_name:
        plot_satellite_location(satellite_data, satellite_name)


def main():

    global satellite_data
    global entry

    root = tk.Tk()
    root.title('Satellite Location Viewer')
    root.geometry('300x200')

    label = tk.Label(root, text='Enter Satellite Name:')
    label.pack()

    entry = tk.Entry(root)
    entry.pack()

    submit_button = tk.Button(root, text='Submit', command=on_submit)
    submit_button.pack()

    file_button = tk.Button(root, text='Select File', command=select_file)
    file_button.pack()

    root.mainloop()


if __name__ == "__main__":
    output_lines = call_cpp_program()

    file_path = 'OUT.txt'
    satellite_data = read_satellite_data(output_lines)
    main()
