"""F722-2020 flight controller, Rev B: single source of truth for parts, nets and placement.

Rev B applies the noise-review fixes:
  - MPU6000 has no VLOGIC (pin 8 is /CS); exposed pad left unsoldered (paste removed on the PCB)
  - Bucks: MAX17572 (4.5-60 V, 1 A, synchronous, fixed-frequency PWM), RT = 19.1k -> 1 MHz, 3x3 mm package
  - Vertical JST-SH plugs (cables exit downward to the ESC), smaller USB diode, to fit the 26.5 mm board
  - Gyro LDO: TPS7A2033 behind a ferrite + 10 uF pi-filter
  - OSD: 27 MHz crystal added, ferrite-fed 3.3 V branch, 0.1 uF on each supply pin, VIN coupling cap
  - VDDA ferrite + 1 uF + 100 nF; 47 ohm series resistors on all 8 motor outputs
  - TVS + bulk at the ESC plug; flyback diode on the buzzer; LC filters on camera and VTX power pads
  - Barometer: BMP280 (DPS310 out of stock), moved away from the LDOs
  - FLASH_CS moved from PC5 to PC3: PC5 is not bonded out on the STM32F722 LQFP64 (PINIO2 dropped)
Each part: ref, lib_id, value, footprint, {pin_number: net}, group (schematic block), place (x, y, side, rot) or ('near', ref, side).
Board coordinates: mm from board centre, +x right, +y towards the front edge (USB / camera pads), as seen from the top.
"""
FP = {
    'R0402': 'Resistor_SMD:R_0402_1005Metric', 'C0402': 'Capacitor_SMD:C_0402_1005Metric',
    'R0201': 'Resistor_SMD:R_0201_0603Metric', 'C0201': 'Capacitor_SMD:C_0201_0603Metric', 'L0201': 'Inductor_SMD:L_0201_0603Metric',
    'C0603': 'Capacitor_SMD:C_0603_1608Metric', 'C0805': 'Capacitor_SMD:C_0805_2012Metric', 'C1206': 'Capacitor_SMD:C_1206_3216Metric',
    'L0402': 'Inductor_SMD:L_0402_1005Metric', 'L0805': 'Inductor_SMD:L_0805_2012Metric', 'L4040': 'Inductor_SMD:L_Taiyo-Yuden_MD-4040', 'L3030': 'Inductor_SMD:L_Taiyo-Yuden_MD-3030',
    'LED0603': 'LED_SMD:LED_0603_1608Metric', 'TP': 'TestPoint:TestPoint_Pad_1.5x1.5mm',
}
parts = []
def P(ref, lib, value, fp, pins, group, place):
    parts.append(dict(ref=ref, lib=lib, value=value, fp=fp, pins=pins, group=group, place=place))
def R(ref, value, a, b, group, place, fp='R0201'): P(ref, 'Device:R', value, FP[fp], {'1': a, '2': b}, group, place)
def C(ref, value, a, b, group, place, fp='C0201'): P(ref, 'Device:C', value, FP[fp], {'1': a, '2': b}, group, place)
def L(ref, value, a, b, group, place, fp): P(ref, 'Device:L', value, FP[fp], {'1': a, '2': b}, group, place)
def FB(ref, a, b, group, place): P(ref, 'Device:FerriteBead_Small', '600R@100MHz', FP['L0201'], {'1': a, '2': b}, group, place)
def near(ref, side='F'): return ('near', ref, side)

# ---------------- MCU ----------------
mcu = {'1': '+3V3', '2': 'LED0', '3': 'LED1', '4': 'BEEPER', '5': 'HSE_IN', '6': 'HSE_OUT', '7': 'NRST',
       '8': 'VBAT_SENSE', '9': 'CURR_SENSE', '10': 'RSSI', '11': 'FLASH_CS', '12': 'GND', '13': 'VDDA',
       '14': 'M5_MCU', '15': 'M6_MCU', '16': 'UART2_TX', '17': 'UART2_RX', '18': 'GND', '19': '+3V3',
       '20': 'GYRO_CS', '21': 'SPI1_SCK', '22': 'SPI1_MISO', '23': 'SPI1_MOSI', '24': 'GYRO_INT',
       '25': 'M1_MCU', '26': 'M2_MCU', '27': 'PINIO1', '28': 'UART3_TX', '29': 'UART3_RX', '30': 'VCAP1',
       '31': 'GND', '32': '+3V3', '33': 'OSD_CS', '34': 'SPI2_SCK', '35': 'SPI2_MISO', '36': 'SPI2_MOSI',
       '37': 'UART6_TX', '38': 'UART6_RX', '39': 'M3_MCU', '40': 'M4_MCU', '41': 'LED_STRIP_MCU',
       '42': 'UART1_TX', '43': 'UART1_RX', '44': 'USB_DM', '45': 'USB_DP', '46': 'SWDIO', '47': 'GND',
       '48': '+3V3', '49': 'SWCLK', '50': 'CAM_CTRL_MCU', '51': 'UART4_TX', '52': 'UART4_RX',
       '53': 'UART5_TX', '54': 'UART5_RX', '55': 'SPI3_SCK', '56': 'SPI3_MISO', '57': 'SPI3_MOSI',
       '58': 'M7_MCU', '59': 'M8_MCU', '60': 'BOOT0', '61': 'I2C1_SCL', '62': 'I2C1_SDA', '63': 'GND', '64': '+3V3'}
P('U1', 'MCU_ST_STM32F7:STM32F722RETx', 'STM32F722RET6', 'Package_QFP:LQFP-64_10x10mm_P0.5mm', mcu, 'MCU', (0, -2.5, 'F', 0))
for i, ref in enumerate(['C1', 'C2', 'C3', 'C4']):
    C(ref, '100nF', '+3V3', 'GND', 'MCU', near('U1'))
C('C5', '4.7uF', '+3V3', 'GND', 'MCU', near('U1'), fp='C0603')
C('C6', '2.2uF', 'VCAP1', 'GND', 'MCU', near('U1'), fp='C0603')
FB('FB1', '+3V3', 'VDDA', 'MCU', near('U1'))
C('C7', '1uF', 'VDDA', 'GND', 'MCU', near('U1'), fp='C0402')
C('C8', '100nF', 'VDDA', 'GND', 'MCU', near('U1'))
C('C9', '100nF', 'NRST', 'GND', 'MCU', near('U1'))
R('R1', '10k', 'BOOT0', 'GND', 'MCU', near('U1'))
P('SW1', 'Switch:SW_Push', 'BOOT', 'Button_Switch_SMD:SW_SPST_B3U-1000P', {'1': '+3V3', '2': 'BOOT0'}, 'MCU', ('near', 'U1', 'B', 'rear'))
P('Y1', 'Device:Crystal_GND24', '8MHz', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
  {'1': 'HSE_IN', '2': 'GND', '3': 'HSE_OUT', '4': 'GND'}, 'MCU', (-8.3, -4.5, 'F', 90))
C('C10', '10pF', 'HSE_IN', 'GND', 'MCU', near('Y1'))
C('C11', '10pF', 'HSE_OUT', 'GND', 'MCU', near('Y1'))
R('R2', '10k', 'GYRO_CS', '+3V3', 'MCU', near('U1'))
R('R3', '10k', 'FLASH_CS', '+3V3', 'MCU', near('U1'))
R('R4', '10k', 'OSD_CS', '+3V3', 'MCU', near('U1'))
R('R5', '2.2k', 'I2C1_SDA', '+3V3', 'MCU', near('U1'))
R('R6', '2.2k', 'I2C1_SCL', '+3V3', 'MCU', near('U1'))

# ---------------- Gyro ----------------
P('U2', 'Sensor_Motion:MPU-6000', 'MPU-6000', 'Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm',
  {'1': 'GND', '6': None, '7': None, '8': 'GYRO_CS', '9': 'SPI1_MISO', '10': 'GYRO_REGOUT', '11': 'GND', '12': 'GYRO_INT',
   '13': '+3V3_GYRO', '18': 'GND', '20': 'GYRO_CPOUT', '23': 'SPI1_SCK', '24': 'SPI1_MOSI'}, 'Gyro', (0, 6.5, 'F', 0))
C('C12', '100nF', '+3V3_GYRO', 'GND', 'Gyro', near('U2'))
C('C13', '100nF', 'GYRO_REGOUT', 'GND', 'Gyro', near('U2'))
C('C14', '2.2nF 50V', 'GYRO_CPOUT', 'GND', 'Gyro', near('U2'), fp='C0402')
FB('FB2', '+5V', '+5V_GYRO', 'Gyro', near('U9'))
C('C15', '10uF', '+5V_GYRO', 'GND', 'Gyro', near('U9'), fp='C0603')
P('U9', 'fc:TPS7A2033PDBV', 'TPS7A2033PDBV', 'Package_TO_SOT_SMD:SOT-23-5',
  {'1': '+5V_GYRO', '2': 'GND', '3': '+5V_GYRO', '4': None, '5': '+3V3_GYRO'}, 'Gyro', (-4.5, 9.2, 'F', 0))
C('C16', '1uF', '+3V3_GYRO', 'GND', 'Gyro', near('U9'), fp='C0402')

# ---------------- Baro, flash ----------------
P('U5', 'Sensor_Pressure:BMP280', 'BMP280', 'Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering',
  {'1': 'GND', '2': '+3V3', '3': 'I2C1_SDA', '4': 'I2C1_SCL', '5': 'GND', '6': '+3V3', '7': 'GND', '8': '+3V3'},
  'Baro + flash', (-8.5, 4.5, 'F', 0))
C('C17', '100nF', '+3V3', 'GND', 'Baro + flash', near('U5'))
P('U4', 'Memory_Flash:W25Q128JVS', 'W25Q128JVPIQ', 'Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4mm',
  {'1': 'FLASH_CS', '2': 'SPI3_MISO', '3': '+3V3', '4': 'GND', '5': 'SPI3_MOSI', '6': 'SPI3_SCK', '7': '+3V3', '8': '+3V3'},
  'Baro + flash', (8.0, 4.6, 'F', 90))
C('C18', '100nF', '+3V3', 'GND', 'Baro + flash', near('U4'))

# ---------------- OSD ----------------
osd = {'3': '+3V3_OSD', '4': 'GND', '5': 'OSD_XI', '6': 'OSD_XO', '7': None, '8': 'OSD_CS', '9': 'SPI2_MOSI', '10': 'SPI2_SCK',
       '11': 'SPI2_MISO', '12': None, '13': None, '17': None, '18': None, '19': 'OSD_RST', '20': 'GND', '21': '+3V3_OSD',
       '22': 'OSD_VIN', '23': 'GND', '24': '+3V3_OSD', '25': 'VID_OUT', '26': 'VID_OUT', '29': 'GND'}
for n in ['1', '2', '14', '15', '16', '27', '28']: osd[n] = None
P('U3', 'fc:AT7456E', 'AT7456E', 'Package_SO:TSSOP-28-1EP_4.4x9.7mm_P0.65mm', osd, 'OSD', (0, -2.45, 'B', 0))
FB('FB3', '+3V3', '+3V3_OSD', 'OSD', near('U3', 'B'))
C('C19', '10uF', '+3V3_OSD', 'GND', 'OSD', near('U3', 'B'), fp='C0603')
for ref in ['C20', 'C21', 'C22']: C(ref, '100nF', '+3V3_OSD', 'GND', 'OSD', near('U3', 'B'))
R('R7', '10k', 'OSD_RST', '+3V3_OSD', 'OSD', near('U3', 'B'))
C('C23', '100nF', 'VID_IN', 'OSD_VIN', 'OSD', near('U3', 'B'))
P('Y2', 'Device:Crystal_GND24', '27MHz', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
  {'1': 'OSD_XI', '2': 'GND', '3': 'OSD_XO', '4': 'GND'}, 'OSD', ('near', 'U3', 'B', 'rear'))
C('C24', '22pF', 'OSD_XI', 'GND', 'OSD', near('Y2', 'B'))
C('C25', '22pF', 'OSD_XO', 'GND', 'OSD', near('Y2', 'B'))

# ---------------- Power input, bucks ----------------
P('J1', 'Connector_Generic:Conn_01x08', 'ESC', 'Connector_JST:JST_SH_BM08B-SRSS-TB_1x08-1MP_P1.00mm_Vertical',
  {'1': 'VBAT', '2': 'GND', '3': 'CURR_SENSE', '4': 'UART4_RX', '5': 'M1', '6': 'M2', '7': 'M3', '8': 'M4'},
  'Connectors', ('edge', 0, -10.9, 'B', 'rear'))
P('D1', 'Device:D_TVS', 'SMF33A', 'Diode_SMD:D_SOD-123F', {'1': 'VBAT', '2': 'GND'}, 'Power input', ('near', 'J1', 'B'))
R('R8', '10k', 'VBAT', 'VBAT_SENSE', 'Power input', near('U1'), fp='R0402')
R('R9', '1k', 'VBAT_SENSE', 'GND', 'Power input', near('U1'))
C('C26', '100nF', 'VBAT_SENSE', 'GND', 'Power input', near('U1'))
C('C27', '100nF', 'CURR_SENSE', 'GND', 'Power input', near('U1'))
C('C28', '100nF', 'RSSI', 'GND', 'Power input', near('U1'))
def buck(n, out, side_x, L_val, r_top, r_bot, en_net, lref, uref, refs, pref):
    cin1, cin2, cvcc, cbst, css, cext, co1, co2 = refs['C']
    rrt, rext, rtop, rbot = refs['R']
    g = f'{out} buck'
    P(uref, 'Regulator_Switching:MAX17572', 'MAX17572', 'Package_DFN_QFN:DFN-12-1EP_3x3mm_P0.5mm_EP2.05x2.86mm',
      {'1': 'VBAT', '2': en_net, '3': None, '4': f'SS{n}', '5': f'VCC{n}', '6': f'RT{n}', '7': f'FB{n}', '8': 'GND',
       '9': f'EXTVCC{n}', '10': f'BST{n}', '11': f'SW{n}', '12': 'GND', '13': 'GND'}, g, ('near', 'U3', 'B', pref))
    C(cin1, '4.7uF 50V', 'VBAT', 'GND', g, near(uref, 'B'), fp='C1206')
    C(cin2, '100nF 50V', 'VBAT', 'GND', g, near(uref, 'B'), fp='C0402')
    C(cvcc, '4.7uF 10V', f'VCC{n}', 'GND', g, near(uref, 'B'), fp='C0603')
    C(cbst, '100nF', f'BST{n}', f'SW{n}', g, near(uref, 'B'))
    C(css, '5.6nF', f'SS{n}', 'GND', g, near(uref, 'B'))
    C(cext, '100nF', f'EXTVCC{n}', 'GND', g, near(uref, 'B'))
    R(rrt, '19.1k', f'RT{n}', 'GND', g, near(uref, 'B'))
    R(rext, '4.7R', out, f'EXTVCC{n}', g, near(uref, 'B'))
    R(rtop, r_top, out, f'FB{n}', g, near(uref, 'B'))
    R(rbot, r_bot, f'FB{n}', 'GND', g, near(uref, 'B'))
    L(lref, L_val, f'SW{n}', out, g, near(uref, 'B'), 'L3030')
    C(co1, '22uF 25V', out, 'GND', g, near(lref, 'B'), fp='C0805')
    C(co2, '22uF 25V', out, 'GND', g, near(lref, 'B'), fp='C0805')
buck(5, '+5V', -6.0, '10uH', '178k', '39k', 'VBAT', 'L1', 'U6',
     {'C': ['C29', 'C30', 'C31', 'C32', 'C33', 'C34', 'C35', 'C36'], 'R': ['R10', 'R11', 'R12', 'R13']}, 'left')
buck(10, '+10V', 6.0, '10uH', '200k', '19.6k', 'EN10', 'L2', 'U7',
     {'C': ['C37', 'C38', 'C39', 'C40', 'C41', 'C42', 'C43', 'C44'], 'R': ['R14', 'R15', 'R16', 'R17']}, 'right')
R('R18', '1k', 'PINIO1', 'EN10', '+10V buck', near('U7', 'B'))
R('R19', '100k', 'EN10', 'GND', '+10V buck', near('U7', 'B'))

# ---------------- LDO (MCU rail), USB ----------------
P('U8', 'Regulator_Linear:TLV75533PDBV', 'TLV75533PDBV', 'Package_TO_SOT_SMD:SOT-23-5',
  {'1': '+5V', '2': 'GND', '3': '+5V', '4': None, '5': '+3V3'}, 'MCU 3.3 V', (4.5, 9.2, 'F', 0))
C('C45', '1uF', '+5V', 'GND', 'MCU 3.3 V', near('U8'), fp='C0402')
C('C46', '1uF', '+3V3', 'GND', 'MCU 3.3 V', near('U8'), fp='C0402')
P('J4', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
  {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'S1': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
   'A5': 'USB_CC1', 'B5': 'USB_CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DM', 'B7': 'USB_DM', 'A8': None, 'B8': None},
  'USB', ('edge', 0, 11.0, 'B', 'front'))
R('R20', '5.1k', 'USB_CC1', 'GND', 'USB', near('J4', 'B'))
R('R21', '5.1k', 'USB_CC2', 'GND', 'USB', near('J4', 'B'))
P('U10', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6',
  {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '2': 'GND', '5': 'VBUS'}, 'USB', near('J4', 'B'))
P('D2', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', {'1': '+5V', '2': 'VBUS'}, 'USB', near('J4', 'B'))

# ---------------- Outputs: fuse, LEDs, buzzer, filters ----------------
P('F1', 'Device:Polyfuse', '1A hold', 'Fuse:Fuse_1206_3216Metric', {'1': '+5V', '2': '+5V_OUT'}, 'Outputs', near('J4', 'B'))
R('R22', '1k', '+3V3', 'LED0_A', 'Outputs', near('D4'))
P('D4', 'Device:LED', 'Blue', FP['LED0603'], {'1': 'LED0', '2': 'LED0_A'}, 'Outputs', (-7.2, 8.4, 'F', 0))
R('R23', '1k', '+3V3', 'LED1_A', 'Outputs', near('D5'))
P('D5', 'Device:LED', 'Green', FP['LED0603'], {'1': 'LED1', '2': 'LED1_A'}, 'Outputs', (7.2, 8.4, 'F', 0))
R('R24', '100R', 'BEEPER', 'BEEPER_G', 'Outputs', near('Q1', 'B'))
R('R25', '10k', 'BEEPER_G', 'GND', 'Outputs', near('Q1', 'B'))
P('Q1', 'Transistor_FET:AO3400A', 'AO3400A', 'Package_TO_SOT_SMD:SOT-23', {'1': 'BEEPER_G', '2': 'GND', '3': 'BUZZER_N'},
  'Outputs', ('near', 'U7', 'B', 'right'))
P('D3', 'Device:D', 'BAT54', 'Diode_SMD:D_SOD-323', {'1': '+5V_OUT', '2': 'BUZZER_N'}, 'Outputs', near('Q1', 'B'))
R('R26', '330R', 'LED_STRIP_MCU', 'LED_DATA', 'Outputs', near('U1'))
R('R27', '330R', 'CAM_CTRL_MCU', 'CAM_CTRL', 'Outputs', near('U1'))
for i in range(1, 9):
    R(f'R{27 + i}', '47R', f'M{i}_MCU', f'M{i}', 'Motor outputs', near('U1', 'B' if i <= 4 else 'F'))
L('L3', '2.2uH', '+5V', 'CAM_5V', 'Outputs', ('near', 'J4', 'F'), 'L0805')
C('C47', '22uF 25V', 'CAM_5V', 'GND', 'Outputs', ('near', 'L3', 'F'), fp='C0805')
P('JP1', 'Jumper:SolderJumper_3_Open', 'VTX 10V/5V', 'Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm',
  {'1': '+10V', '2': 'VTX_PWR_SEL', '3': '+5V'}, 'Outputs', ('near', 'J4', 'F'))
L('L4', '2.2uH', 'VTX_PWR_SEL', 'VTX_PWR', 'Outputs', ('near', 'JP1', 'F'), 'L0805')
C('C48', '22uF 25V', 'VTX_PWR', 'GND', 'Outputs', ('near', 'L4', 'F'), fp='C0805')

# ---------------- Connectors ----------------
P('J2', 'Connector_Generic:Conn_01x06', 'HD VTX', 'Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical',
  {'1': '+10V', '2': 'GND', '3': 'UART1_TX', '4': 'UART1_RX', '5': 'GND', '6': 'UART2_RX'}, 'Connectors', ('edge', 10.9, 0, 'B', 'right'))
P('J3', 'Connector_Generic:Conn_01x06', 'GPS', 'Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical',
  {'1': '+5V_OUT', '2': 'GND', '3': 'UART3_TX', '4': 'UART3_RX', '5': 'I2C1_SDA', '6': 'I2C1_SCL'}, 'Connectors', ('edge', -10.9, 0, 'B', 'left'))

# ---------------- Edge pads (top side, 2.0 mm pitch) ----------------
EDGE = {
    'L': ['+5V_OUT', 'GND', 'UART2_TX', 'UART2_RX', '+5V_OUT', 'GND', 'UART6_TX', 'UART6_RX'],
    'R': ['+5V_OUT', 'GND', 'UART5_TX', 'UART5_RX', 'RSSI', 'LED_DATA', 'BUZZER_N', '+5V_OUT'],
    'F': ['CAM_5V', 'GND', 'VID_IN', 'CAM_CTRL', 'VID_OUT', 'VTX_PWR', 'GND', 'UART4_TX'],
    'B': ['M5', 'M6', 'M7', 'M8', 'I2C1_SDA', 'I2C1_SCL', 'SWDIO', 'SWCLK'],
}
EDGE_LABEL = {
    'L': ['5V', 'GND', 'T2', 'R2', '5V', 'GND', 'T6', 'R6'], 'R': ['5V', 'GND', 'T5', 'R5', 'RSSI', 'LED', 'BZ-', 'BZ+'],
    'F': ['CAM', 'GND', 'VIN', 'CC', 'VOUT', 'VTX', 'GND', 'TX4'], 'B': ['M5', 'M6', 'M7', 'M8', 'SDA', 'SCL', 'DIO', 'CLK'],
}
tp = 1
for edge, nets in EDGE.items():
    for i, net in enumerate(nets):
        c = -7 + 2 * i
        x, y = {'L': (-12.2, c), 'R': (12.2, c), 'F': (c, 12.2), 'B': (c, -12.2)}[edge]
        P(f'TP{tp}', 'Connector:TestPoint', EDGE_LABEL[edge][i], FP['TP'], {'1': net}, 'Edge pads', (x, y, 'F', 0))
        tp += 1
P('TP33', 'Connector:TestPoint', 'NRST', FP['TP'], {'1': 'NRST'}, 'Edge pads', near('U1', 'B'))

# Mounting holes (no electrical pins)
for i, (x, y) in enumerate([(-10, -10), (10, -10), (-10, 10), (10, 10)], start=1):
    P(f'H{i}', 'Mechanical:MountingHole', 'M2', 'MountingHole:MountingHole_2.2mm_M2', {}, 'Mechanical', (x, y, 'F', 0))

# Nets that need a PWR_FLAG (driven through passives or off-board)
PWR_FLAGS = ['VBAT', 'GND', '+5V', 'VDDA', '+3V3_OSD', '+5V_GYRO', 'EXTVCC5', 'EXTVCC10', 'VBUS', '+5V_OUT', '+10V']
GROUP_ORDER = ['MCU', 'Gyro', 'Baro + flash', 'OSD', 'Power input', '+5V buck', '+10V buck', 'MCU 3.3 V', 'USB',
               'Outputs', 'Motor outputs', 'Connectors', 'Edge pads', 'Mechanical']
