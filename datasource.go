package plugin

import (
	"context"
	"encoding/json"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/data"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "grafana-simple-grpc-datasource/pkg/proto/v3"
)

var (
	_ backend.QueryDataHandler      = (*Datasource)(nil)
	_ backend.CheckHealthHandler    = (*Datasource)(nil)
	_ instancemgmt.InstanceDisposer = (*Datasource)(nil)
)

func NewDatasource(_ backend.DataSourceInstanceSettings) (instancemgmt.Instance, error) {
	return &Datasource{}, nil
}

type Datasource struct{}
func (d *Datasource) Dispose() {}

// Models for our JSON Data
type LogEntry struct {
	Time             string  `json:"Time"`
	BE_State         *string `json:"BE_State"`
	Thermal_Throttle *string `json:"Thermal_Throttle"`
	Smart_Alert      *string `json:"Smart_Alert"`
	FWQ              *string `json:"FWQ"`
	CFS              *string `json:"CFS"`
	AEN              *string `json:"AEN"`
}

func (d *Datasource) QueryData(ctx context.Context, req *backend.QueryDataRequest) (*backend.QueryDataResponse, error) {
	response := backend.NewQueryDataResponse()
	for _, q := range req.Queries {
		response.Responses[q.RefID] = d.query(ctx, req.PluginContext, q)
	}
	return response, nil
}

func (d *Datasource) query(ctx context.Context, pCtx backend.PluginContext, query backend.DataQuery) backend.DataResponse {
	var response backend.DataResponse

	// 1. Read what Grafana is asking for
	var qm struct {
		QueryType   string `json:"queryType"`
		TicketId    string `json:"ticketId"`
		TelemetryId string `json:"telemetryId"`
	}
	json.Unmarshal(query.JSON, &qm)

	// If it's a variable query from the dashboard settings, it might just send ticketId
	if qm.QueryType == "" && qm.TicketId != "" {
		qm.QueryType = "variable"
	}

	// 2. Connect to Python
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		response.Error = err
		return response
	}
	defer conn.Close()
	client := pb.NewCommandServiceClient(conn)

	// 3. Decide which Python command to run
	cmdName := "GetLogs"
	if qm.QueryType == "variable" {
		cmdName = "GetTelemetryIDs"
	}

	initReq := &pb.Command_Initialize_Request{
		CommandName: cmdName,
		CommandArguments: map[string]string{
			"TicketID":    qm.TicketId,
			"TelemetryID": qm.TelemetryId,
		},
	}
	initRes, err := client.InitiateCommand(ctx, initReq)
	if err != nil {
		response.Error = err
		return response
	}

	execReq := &pb.Command_Execute_Request{CommandId: initRes.CommandId, RunAsync: false}
	execRes, err := client.ExecuteCommand(ctx, execReq)
	if err != nil {
		response.Error = err
		return response
	}

	jsonString := execRes.GetSyncResponse().GetRespData()

	// 4. Process Dropdown (Variable) Data
	if qm.QueryType == "variable" {
		var ids []string
		json.Unmarshal([]byte(jsonString), &ids)
		
		field := data.NewField("text", nil, ids)
		frame := data.NewFrame("TelemetryIDs", field)
		response.Frames = append(response.Frames, frame)
		return response
	}

	// 5. Process Timeline Graph Data (Replicating your SQL structure)
	var logs []LogEntry
	json.Unmarshal([]byte(jsonString), &logs)

	timeField := data.NewField("Time", nil, make([]time.Time, len(logs)))
	beStateField := data.NewField("BE_State", nil, make([]*string, len(logs)))
	thermalField := data.NewField("Thermal_Throttle", nil, make([]*string, len(logs)))
	smartAlertField := data.NewField("Smart_Alert", nil, make([]*string, len(logs)))
	fwqField := data.NewField("FWQ", nil, make([]*string, len(logs)))
	cfsField := data.NewField("CFS", nil, make([]*string, len(logs)))
	aenField := data.NewField("AEN", nil, make([]*string, len(logs)))

	for i, logItem := range logs {
		parsedTime, _ := time.Parse("15:04:05", logItem.Time)
		now := time.Now()
		finalTime := time.Date(now.Year(), now.Month(), now.Day(), parsedTime.Hour(), parsedTime.Minute(), parsedTime.Second(), 0, time.UTC)
		
		timeField.Set(i, finalTime)
		beStateField.Set(i, logItem.BE_State)
		thermalField.Set(i, logItem.Thermal_Throttle)
		smartAlertField.Set(i, logItem.Smart_Alert)
		fwqField.Set(i, logItem.FWQ)
		cfsField.Set(i, logItem.CFS)
		aenField.Set(i, logItem.AEN)
	}

	frame := data.NewFrame("Timeline Data", timeField, beStateField, thermalField, smartAlertField, fwqField, cfsField, aenField)
	response.Frames = append(response.Frames, frame)

	return response
}

func (d *Datasource) CheckHealth(_ context.Context, req *backend.CheckHealthRequest) (*backend.CheckHealthResult, error) {
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return &backend.CheckHealthResult{Status: backend.HealthStatusError, Message: "Error"}, nil
	}
	defer conn.Close()
	return &backend.CheckHealthResult{Status: backend.HealthStatusOk, Message: "OK"}, nil
}
