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
	"sbleedyGonzales/bleagle/gatt/pretty"
)

var (
	scanning = true
	rssiThreshold int
	hciDevice int
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
	trimmedPath := strings.Replace(workingDir, "/modules/BLEagle/gatt", "", 1)
	fullPath := filepath.Join(trimmedPath, "results/discovered_devices.json")

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
	flag.IntVar(&hciDevice, "d", -1, "HCI Device (optional)")
	flag.Parse()

	clientOptions := []gatt.Option{
		gatt.LnxMaxConnections(1),
		gatt.LnxDeviceID(hciDevice, true),
	}

	d, err := gatt.NewDevice(clientOptions...)
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
	save_to_file()
}