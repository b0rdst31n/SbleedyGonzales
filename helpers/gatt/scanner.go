// +build

package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"
	"sort"
	"regexp"
	"strconv"

	"github.com/evilsocket/islazy/ops"
	"github.com/bettercap/gatt"
	"github.com/bettercap/gatt/examples/option"
	"sbleedy/gatt/pretty"
)

var (
	scanning = true
	rssiThreshold int
	colNames = []string{"RSSI", "MAC", "Name", "Vendor", "Flags", "Connectable"}
	rows = make([][]string, 0)
	discoveredDevices = make([]BLEDevice, 0)
	lastUpdateTimes = make(map[string]time.Time)
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
		d.Scan([]gatt.UUID{}, true)
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

func extractRSSI(value string) (int, error) {
	ansiRegex := regexp.MustCompile(`\x1b\[[0-9;]*m`)
	cleanedValue := ansiRegex.ReplaceAllString(value, "")
	cleanedValue = strings.TrimSpace(strings.TrimSuffix(cleanedValue, " dBm"))
	return strconv.Atoi(cleanedValue)
}

func updateOrAddRow(rows *[][]string, newRow []string, addressIndex int) {
	for i, row := range *rows {
		if row[addressIndex] == newRow[addressIndex] {
			(*rows)[i] = newRow
			return
		}
	}
	*rows = append(*rows, newRow)
}

func onPeriphDiscovered(p gatt.Peripheral, a *gatt.Advertisement, rssi int) {
	if rssiThreshold != 0 && rssi < rssiThreshold {
		return // Ignore devices with RSSI below the threshold
	}

	address := p.ID()
	currentTime := time.Now()

	if lastUpdate, exists := lastUpdateTimes[address]; exists {
		if currentTime.Sub(lastUpdate) < 5*time.Second {
			return
		}
	}

	lastUpdateTimes[address] = currentTime

	cmd := exec.Command("clear")
	cmd.Stdout = os.Stdout
	cmd.Run()

	rssiString := colorRSSI(rssi)
	vendor := a.Company
	if a.Company == "" && a.CompanyID != 0 {
		a.Company = pretty.CompanyIdents[a.CompanyID]
		vendor = pretty.Dim(a.Company)
	}
	isConnectable := ops.Ternary(a.Connectable, pretty.Green("✔"), pretty.Red("✖")).(string)

	updateOrAddRow(&rows, []string{
		rssiString,
		address,
		pretty.Yellow(a.LocalName),
		vendor,
		a.Flags.String(),
		isConnectable,
	}, 1)

	sort.Slice(rows, func(i, j int) bool {
		rssiI, errI := extractRSSI(rows[i][0])
		rssiJ, errJ := extractRSSI(rows[j][0])
		if errI != nil || errJ != nil {
			return rows[i][0] > rows[j][0]
		}
		return rssiI > rssiJ
	})

	pretty.Table(os.Stdout, colNames, rows)

	time.Sleep(2 * time.Second)
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
}