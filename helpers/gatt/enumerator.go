// +build

package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"strconv"
	"time"
	"encoding/json"
	"encoding/binary"
	"path/filepath"

	"github.com/bettercap/gatt"
	"github.com/bettercap/gatt/examples/option"
	"attackable/bleagle/gatt/pretty"
)

type BLECharacteristic struct {
	UUID       string      `json:"uuid"`
	Name       string      `json:"name"`
	Handle     uint16      `json:"handle"`
	Properties []string    `json:"properties"`
	Data       interface{} `json:"data"`
}

type BLEService struct {
	UUID            string              `json:"uuid"`
	Name            string              `json:"name"`
	Handle          uint16              `json:"handle"`
	EndHandle       uint16              `json:"end_handle"`
	Characteristics []BLECharacteristic `json:"characteristics"`
}

var (
	macAddress string
	handle     string
	writeData       string
	done       = make(chan struct{})
	current_services = make([]BLEService, 0)
	columns = []string{"Handles", "Service > Characteristics", "Properties", "Data"}
	rows = make([][]string, 0)
	wantsToWrite bool
	foundToWrite bool
	isConnected = false
)

func parseProperties(c *gatt.Characteristic) (props []string, isReadable bool, isWritable bool, withResponse bool) {
	isReadable = false
	isWritable = false
	withResponse = false
	props = make([]string, 0)
	mask := c.Properties()

	if (mask & gatt.CharBroadcast) != 0 {
		props = append(props, "BCAST")
	}
	if (mask & gatt.CharRead) != 0 {
		isReadable = true
		props = append(props, "READ")
	}
	if (mask&gatt.CharWriteNR) != 0 || (mask&gatt.CharWrite) != 0 {
		props = append(props, "WRITE")
		isWritable = true
		withResponse = (mask & gatt.CharWriteNR) == 0
	}
	if (mask & gatt.CharNotify) != 0 {
		props = append(props, "NOTIFY")
	}
	if (mask & gatt.CharIndicate) != 0 {
		props = append(props, "INDICATE")
	}
	if (mask & gatt.CharSignedWrite) != 0 {
		props = append(props, "SIGN WRITE")
		isWritable = true
		withResponse = true
	}
	if (mask & gatt.CharExtended) != 0 {
		props = append(props, "X")
	}

	return
}

func parseRawData(raw []byte) string {
	s := ""
	for _, b := range raw {
		if strconv.IsPrint(rune(b)) {
			s += pretty.Yellow(string(b))
		} else {
			s += pretty.Dim(fmt.Sprintf("%02x", b))
		}
	}
	return s
}

// org.bluetooth.characteristic.gap.appearance
func parseAppearance(raw []byte) string {
	app := binary.LittleEndian.Uint16(raw[0:2])
	if appName, found := pretty.AppearanceUUIDS[app]; found {
		return pretty.Green(appName)
	}
	return fmt.Sprintf("0x%x", app)
}

// org.bluetooth.characteristic.pnp_id
func parsePNPID(raw []byte) []string {
	vendorIdSrc := byte(raw[0])
	vendorId := binary.LittleEndian.Uint16(raw[1:3])
	prodId := binary.LittleEndian.Uint16(raw[3:5])
	prodVer := binary.LittleEndian.Uint16(raw[5:7])

	src := ""
	if vendorIdSrc == 1 {
		src = " (Bluetooth SIG assigned Company Identifier)"
	} else if vendorIdSrc == 2 {
		src = " (USB Implementer’s Forum assigned Vendor ID value)"
	}

	return []string{
		pretty.Green("Vendor ID") + fmt.Sprintf(": 0x%04x%s", vendorId, pretty.Dim(src)),
		pretty.Green("Product ID") + fmt.Sprintf(": 0x%04x", prodId),
		pretty.Green("Product Version") + fmt.Sprintf(": 0x%04x", prodVer),
	}
}

// org.bluetooth.characteristic.gap.peripheral_preferred_connection_parameters
func parseConnectionParams(raw []byte) []string {
	minConInt := binary.LittleEndian.Uint16(raw[0:2])
	maxConInt := binary.LittleEndian.Uint16(raw[2:4])
	slaveLat := binary.LittleEndian.Uint16(raw[4:6])
	conTimeMul := binary.LittleEndian.Uint16(raw[6:8])

	return []string{
		pretty.Green("Connection Interval") + fmt.Sprintf(": %d -> %d", minConInt, maxConInt),
		pretty.Green("Slave Latency") + fmt.Sprintf(": %d", slaveLat),
		pretty.Green("Connection Supervision Timeout Multiplier") + fmt.Sprintf(": %d", conTimeMul),
	}
}

// org.bluetooth.characteristic.gap.peripheral_privacy_flag
func parsePrivacyFlag(raw []byte) string {
	if raw[0] == 0x0 {
		return pretty.Green("Privacy Disabled")
	}
	return pretty.Red("Privacy Enabled")
}

func onStateChanged(d gatt.Device, s gatt.State) {
	fmt.Println("State:", s)
	switch s {
	case gatt.StatePoweredOn:
		fmt.Println("Scanning...")
		d.Scan([]gatt.UUID{}, false)
		timer := time.NewTimer(20 * time.Second)
		go func() {
			<-timer.C
			if !isConnected {
				fmt.Println("Apparently there can't be a connection established to this device (within 20s). Stopping the scan.")
				d.StopScanning()
				os.Exit(0)
			}
		}()
		return
	default:
		d.StopScanning()
	}
}

func onPeriphDiscovered(p gatt.Peripheral, a *gatt.Advertisement, rssi int) {
	if strings.ToUpper(p.ID()) != macAddress {
		return
	}

	// Stop scanning once we've got the peripheral we're looking for.
	p.Device().StopScanning()

	fmt.Printf("\nPeripheral ID:%s, NAME:(%s)\n", p.ID(), p.Name())
	fmt.Println("  Local Name        =", a.LocalName)
	fmt.Println("  TX Power Level    =", a.TxPowerLevel)
	fmt.Println("  Manufacturer Data =", a.ManufacturerData)
	fmt.Println("  Service Data      =", a.ServiceData)
	fmt.Println("")

	p.Device().Connect(p)
}

func onPeriphConnected(p gatt.Peripheral, err error) {
	fmt.Println("Connected")
	isConnected = true
	defer p.Device().CancelConnection(p)

	if err := p.SetMTU(500); err != nil {
		fmt.Printf("Failed to set MTU, err: %s\n", err)
	}

	wantsToWrite = handle != ""
	foundToWrite = false

	handle_uint16 := uint16(0)
	if(wantsToWrite) {
		handle_uint64, err := strconv.ParseUint(handle, 16, 16)
		if err != nil {
			fmt.Println("Error while parsing: %s", err)
		}
		handle_uint16 = uint16(handle_uint64)
	}

	ss, err := p.DiscoverServices(nil)
	if err != nil {
		fmt.Printf("Failed to discover services, err: %s\n", err)
		return
	}

	for _, svc := range ss {
		service := BLEService{
			UUID:            svc.UUID().String(),
			Name:            svc.Name(),
			Handle:          svc.Handle(),
			EndHandle:       svc.EndHandle(),
			Characteristics: make([]BLECharacteristic, 0),
		}

		name := svc.Name()
		if name == "" {
			uuidString := svc.UUID().String()
			uuidInt, err := strconv.ParseInt(uuidString, 16, 32)
			if err != nil {
				name = uuidString
			} else {
				if serviceName, found := pretty.ServiceUUIDS[uuidInt]; found {
					name = fmt.Sprintf("%s (%s)", pretty.Green(serviceName), pretty.Dim(svc.UUID().String()))
				} else {
					name = uuidString
				}
			}
		} else {
			name = fmt.Sprintf("%s (%s)", pretty.Green(name), pretty.Dim(svc.UUID().String()))
		}

		row := []string{
			fmt.Sprintf("%04x -> %04x", svc.Handle(), svc.EndHandle()),
			name,
			"",
			"",
		}

		rows = append(rows, row)

		// Discover characteristics
		cs, err := p.DiscoverCharacteristics(nil, svc)
		if err != nil {
			fmt.Printf("Failed to discover characteristics, err: %s\n", err)
			continue
		}

		for _, c := range cs {
			props, isReadable, isWritable, withResponse := parseProperties(c)

			char := BLECharacteristic{
				UUID:       c.UUID().String(),
				Name:       c.Name(),
				Handle:     c.VHandle(),
				Properties: props,
			}

			name = c.Name()
			if name == "" {
				uuidString := c.UUID().String()
				uuidInt, err := strconv.ParseInt(uuidString, 16, 32)
				if err != nil {
					name = "    " + uuidString
				} else {
					if charName, found := pretty.CharacteristicUUIDS[uuidInt]; found {
						name = fmt.Sprintf("    %s (%s)", pretty.Green(charName), pretty.Dim(c.UUID().String()))
					} else {
						name = "    " + uuidString
					}
				}
			} else {
				name = fmt.Sprintf("    %s (%s)", pretty.Green(name), pretty.Dim(c.UUID().String()))
			}

			if(wantsToWrite) {
				if handle_uint16 == c.VHandle() {
					foundToWrite = true

					hexBytes := []byte(writeData)
					if isWritable {
						fmt.Printf("Writing %v to characteristic %d ...\n", hexBytes, c.VHandle())
					} else {
						fmt.Printf("Attempt to write %v to non writable characteristic %d ...\n", hexBytes, c.VHandle())
					}
					if err := p.WriteCharacteristic(c, hexBytes, !withResponse); err != nil {
						fmt.Printf("Error while writing: %v\n", err)
					}
				}
			}

			sz := 0
			raw := ([]byte)(nil)
			err := error(nil)
			if isReadable {
				if raw, err = p.ReadCharacteristic(c); raw != nil {
					sz = len(raw)
				}
			}

			s := ""
			for _, b := range raw {
				if strconv.IsPrint(rune(b)) {
					s += string(b)
				} else {
					s += fmt.Sprintf("%02x", b)
				}
			}
			char.Data = s

			data := ""
			multi := ([]string)(nil)
			if err != nil {
				data = err.Error()
			} else if c.Name() == "Appearance" && sz >= 2 {
				data = parseAppearance(raw)
			} else if c.Name() == "PnP ID" && sz >= 7 {
				multi = parsePNPID(raw)
			} else if c.Name() == "Peripheral Preferred Connection Parameters" && sz >= 8 {
				multi = parseConnectionParams(raw)
			} else if c.Name() == "Peripheral Privacy Flag" && sz >= 1 {
				data = parsePrivacyFlag(raw)
			} else {
				data = parseRawData(raw)
			}

			if(data == "insufficient authentication") {
				data = pretty.Red(data)
			}

			if multi == nil {
				rows = append(rows, []string{
					fmt.Sprintf("%04x", c.VHandle()),
					name,
					strings.Join(props, ", "),
					data,
				})
			} else {
				for i, m := range multi {
					if i == 0 {
						rows = append(rows, []string{
							fmt.Sprintf("%04x", c.VHandle()),
							name,
							strings.Join(props, ", "),
							m,
						})
					} else {
						rows = append(rows, []string{"", "", "", m})
					}
				}
			}

			service.Characteristics = append(service.Characteristics, char)

			// Subscribe the characteristic, if possible.
			/*if (c.Properties() & (gatt.CharNotify | gatt.CharIndicate)) != 0 {
				f := func(c *gatt.Characteristic, b []byte, err error) {
					fmt.Printf("notified: % X | %q\n", b, b)
				}
				if err := p.SetNotifyValue(c, f); err != nil {
					fmt.Printf("Failed to subscribe characteristic, err: %s\n", err)
					continue
				}
			}*/
		}
		rows = append(rows, []string{"", "", "", ""})
		current_services = append(current_services, service)
	}

	//fmt.Printf("Waiting for 5 seconds to get some notifiations, if any.\n")
	//time.Sleep(5 * time.Second)
}

func save_to_file() {
	if(handle != "") {
		return;
	}

	jsonData, err := json.MarshalIndent(current_services, "", "    ")
	if err != nil {
		fmt.Println("Error marshalling to JSON:", err)
		return
	}

	filename := fmt.Sprintf("ble_services_%s.json", strings.ReplaceAll(macAddress, ":", ""))
	workingDir, err := os.Getwd()
	if err != nil {
		fmt.Println(err) 
		return
	}

	projectDir := strings.TrimSuffix(workingDir, "gatt")
	fullPath := filepath.Join(projectDir, "scanned_devices/" + filename)

	if err := os.MkdirAll(projectDir + "scanned_devices/", os.ModePerm); err != nil {
		fmt.Println("Error creating directory:", err)
		return
	}

	f, err := os.Create(fullPath)
	if err != nil {
		fmt.Println("Error creating file:", err)
		return
	}
	defer f.Close()

	if _, err = f.Write(jsonData); err != nil {
		fmt.Println("Error writing to file:", err)
		return
	}

	fmt.Printf("Data successfully written to %s\n", fullPath)
}

func onPeriphDisconnected(p gatt.Peripheral, err error) {
	if wantsToWrite && !foundToWrite {
		fmt.Printf("Error: writable characteristic with handle %s not found.", handle)
	} else if(!wantsToWrite) {
		pretty.Table(os.Stdout, columns, rows)
	}

	fmt.Println("Disconnected")
	//save_to_file()
	close(done)
}

func main() {
	flag.StringVar(&macAddress, "m", "", "MAC address of the peripheral (required)")
	flag.StringVar(&handle, "h", "", "Handle (optional)")
	flag.StringVar(&writeData, "d", "", "Data (optional)")

	flag.Parse()

	d, err := gatt.NewDevice(option.DefaultClientOptions...)
	if err != nil {
		log.Fatalf("Failed to open device, err: %s\n", err)
		return
	}

	if macAddress == "" {
		log.Fatalf("Error: -m (MAC address) is required.\nUsage: %s -m <mac-address> [-h <handle>] [-d <data>]\n", os.Args[0])
	}

	// Register handlers.
	d.Handle(
		gatt.PeripheralDiscovered(onPeriphDiscovered),
		gatt.PeripheralConnected(onPeriphConnected),
		gatt.PeripheralDisconnected(onPeriphDisconnected),
	)

	d.Init(onStateChanged)
	<-done
	fmt.Println("Done")
}
