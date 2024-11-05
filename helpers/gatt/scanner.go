// +build

package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"
	"path/filepath"
	"encoding/json"

	"github.com/evilsocket/islazy/ops"
	"github.com/bettercap/gatt"
	"github.com/bettercap/gatt/examples/option"
	"attackable/bleagle/gatt/pretty"
)

var (
	scanning = true
	rssiThreshold int
	colNames = []string{"RSSI", "MAC", "Name", "Vendor", "Flags", "Connectable"}
	rows = make([][]string, 0)
	discoveredDevices = make([]BLEDevice, 0)
)

type BLEDevice struct {
	Mac           string `json:"mac"`
	Name          string `json:"name"`
	Vendor        string `json:"vendor"`
	RSSI          int    `json:"rssi"`
	Flags         string `json:"flags"`
	isConnectable bool   `json:"isConnectable"`
}

func onStateChanged(d gatt.Device, s gatt.State) {
	fmt.Println("State:", s)
	switch s {
	case gatt.StatePoweredOn:
		fmt.Println("scanning...")
		d.Scan([]gatt.UUID{}, false)
		return
	default:
		d.StopScanning()
	}
}

func colorRSSI(n int) string {
	// ref. https://www.metageek.com/training/resources/understanding-rssi-2.html
	rssi := fmt.Sprintf("%d dBm", n)
	if n >= -67 {
		rssi = pretty.Green(rssi)
	} else if n >= -70 {
		rssi = pretty.Dim(pretty.Green(rssi))
	} else if n >= -80 {
		rssi = pretty.Yellow(rssi)
	} else {
		rssi = pretty.Dim(pretty.Red(rssi))
	}
	return rssi
}

func onPeriphDiscovered(p gatt.Peripheral, a *gatt.Advertisement, rssi int) {
	if rssiThreshold != 0 && rssi < rssiThreshold {
		return // Ignore devices with RSSI below the threshold
	}

	currDevice := BLEDevice{
		Mac:       	   p.ID(),
		Name:          a.LocalName,
		Vendor:        a.Company,
		RSSI:          rssi,
		Flags:         a.Flags.String(),
		isConnectable: a.Connectable,
	}
	discoveredDevices = append(discoveredDevices, currDevice)

	/*
	green := "\033[32m"
	orange := "\033[38;5;214m"
	reset := "\033[0m"
	var output string
	if a.LocalName != "" {
		output += fmt.Sprintf("\n%sNew BLE device%s %s%s%s detected as %s ", green, reset, orange, a.LocalName, reset, p.ID())
	} else {
		output += fmt.Sprintf("\n%sNew BLE device%s detected as %s", green, reset, p.ID())
	}
	if len(a.ManufacturerData) > 0 {
		companyIdentifier := binary.LittleEndian.Uint16(a.ManufacturerData[0:2])
		if cname, found := gatt.CompanyIdents[companyIdentifier]; found {
			output += fmt.Sprintf(" (%s%s%s) ", orange, cname, reset)
		}
	}
	output += fmt.Sprintf("%d dBm.", rssi)
	fmt.Printf(output)*/
	//fmt.Print("\033[H\033[2J")
	cmd := exec.Command("clear")
    cmd.Stdout = os.Stdout
    cmd.Run()

	rssiString := colorRSSI(rssi)
	address := p.ID()
	vendor := a.Company
	if a.Company == "" && a.CompanyID != 0 {
		a.Company = pretty.CompanyIdents[a.CompanyID]
		vendor = pretty.Dim(a.Company)
	}
	isConnectable := ops.Ternary(a.Connectable, pretty.Green("✔"), pretty.Red("✖")).(string)

	rows = append(rows, []string{
		rssiString,
		address,
		pretty.Yellow(a.LocalName),
		vendor,
		a.Flags.String(),
		isConnectable,
	})

	pretty.Table(os.Stdout, colNames, rows)
	fmt.Print("\nType 'stop' to stop scanning: ")
}

func save_to_file() {
	jsonData, err := json.MarshalIndent(discoveredDevices, "", "    ")
	if err != nil {
		fmt.Println("Error marshalling to JSON:", err)
		return
	}

	workingDir, err := os.Getwd()
	if err != nil {
		fmt.Println(err)
		return
	}
	projectDir := strings.TrimSuffix(workingDir, "gatt")
	fullPath := filepath.Join(projectDir, "scanned_devices/discovered_devices.json")

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

// Goroutine to listen for user input
func listenForStop(d gatt.Device, done chan bool) {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Print("\nType 'stop' to stop scanning")
		input, _ := reader.ReadString('\n')
		input = strings.TrimSpace(input)
		if input == "stop" {
			fmt.Println("Stopping scan...")
			d.StopScanning()
			scanning = false
			done <- true
			break
		}
	}
}

func main() {
	var timeout int
	flag.IntVar(&timeout, "t", 0, "Set scan timeout duration (in seconds).")
	flag.IntVar(&rssiThreshold, "r", 0, "Set RSSI threshold (only show devices with RSSI >= threshold).")
	flag.Parse()

	d, err := gatt.NewDevice(option.DefaultClientOptions...)
	if err != nil {
		log.Fatalf("Failed to open device, err: %s\n", err)
		return
	}

	d.Handle(gatt.PeripheralDiscovered(onPeriphDiscovered))
	d.Init(onStateChanged)

	done := make(chan bool)

	go listenForStop(d, done)

	if timeout > 0 {
		go func() {
			time.Sleep(time.Duration(timeout) * time.Second)
			fmt.Println("\nScan timeout reached. Stopping scan...")
			d.StopScanning()
			scanning = false
			done <- true
		}()
	}

	<-done
	//save_to_file()
}