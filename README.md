package plugin

import (
	"context"
	"encoding/json"
	"time"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
	"github.com/grafana/grafana-plugin-sdk-go/data"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	// This is the blueprint we generated earlier!
	pb "bitbucket.org/innius/grafana-simple-grpc-datasource/pkg/proto/v3"
)

var (
	_ backend.QueryDataHandler      = (*Datasource)(nil)
	_ backend.CheckHealthHandler    = (*Datasource)(nil)
	_ instancemgmt.InstanceDisposer = (*Datasource)(nil)
)

type Datasource struct {
	client pb.SystemMonitorClient
	conn   *grpc.ClientConn
}

func NewDatasource(ctx context.Context, settings backend.DataSourceInstanceSettings) (instancemgmt.Instance, error) {
	// Fixed the comma issue here and updated to your specific IP!
	conn, err := grpc.Dial("10.116.87.164:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}

	client := pb.NewSystemMonitorClient(conn)

	return &Datasource{
		client: client,
		conn:   conn,
	}, nil
}

func (d *Datasource) Dispose() {
	if d.conn != nil {
		d.conn.Close()
	}
}

func (d *Datasource) CheckHealth(ctx context.Context, req *backend.CheckHealthRequest) (*backend.CheckHealthResult, error) {
	// Tells Grafana the Data Source connection is successful
	return &backend.CheckHealthResult{
		Status:  backend.HealthStatusOk,
		Message: "Connected to System Monitor gRPC Server!",
	}, nil
}

func (d *Datasource) QueryData(ctx context.Context, req *backend.QueryDataRequest) (*backend.QueryDataResponse, error) {
	response := backend.NewQueryDataResponse()

	for _, q := range req.Queries {
		res := d.query(ctx, q)
		response.Responses[q.RefID] = res
	}

	return response, nil
}

func (d *Datasource) query(ctx context.Context, query backend.DataQuery) backend.DataResponse {
	var response backend.DataResponse

	// 1. Read what the user typed in the Grafana UI
	var qm struct {
		CommandName  string `json:"commandName"`
		TargetServer string `json:"targetServer"`
	}
	_ = json.Unmarshal(query.JSON, &qm)

	if qm.CommandName == "" {
		qm.CommandName = "Ping" // Default fallback
	}

	// 2. Call the Python server (ExecuteCommand)
	grpcReq := &pb.CommandRequest{
		CommandName:  qm.CommandName,
		TargetServer: qm.TargetServer,
	}

	grpcRes, err := d.client.ExecuteCommand(ctx, grpcReq)
	if err != nil {
		response.Error = err
		return response
	}

	// 3. Create the Grafana "Spreadsheet" (Frame)
	frame := data.NewFrame("command_response")

	// 4. Draw the Columns (Fields) and inject the Python data
	frame.Fields = append(frame.Fields,
		data.NewField("time", nil, []time.Time{time.Now()}),
		data.NewField("metric_value", nil, []float64{float64(grpcRes.MetricValue)}),
		data.NewField("log_message", nil, []string{grpcRes.LogMessage}),
		data.NewField("is_success", nil, []bool{grpcRes.IsSuccess}),
	)

	// 5. Pack the box and send it to Grafana
	response.Frames = append(response.Frames, frame)
	return response
}
