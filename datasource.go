import { DataSourceInstanceSettings } from '@grafana/data';
import { DataSourceWithBackend, getBackendSrv } from '@grafana/runtime';
import { MyQuery, MyDataSourceOptions } from './types';

export class DataSource extends DataSourceWithBackend<MyQuery, MyDataSourceOptions> {
  constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {
    super(instanceSettings);
  }

  // This function silently calls the Go backend to get the Telemetry IDs
  async getTelemetryIds(ticketId: string): Promise<Array<{ label: string; value: string }>> {
    if (!ticketId) return [];

    const request = {
      queries: [
        {
          refId: 'fetch_telemetry',
          datasource: { uid: this.uid },
          queryType: 'variable', // Tells Go to return the dropdown list
          ticketId: ticketId,
        },
      ],
    };

    try {
      const response = await getBackendSrv().post('/api/ds/query', request);
      const frames = response.results['fetch_telemetry'].frames;

      if (frames && frames.length > 0) {
        // Extract the array [8, 9, 10] and turn it into dropdown options
        const values = frames[0].data.values[0];
        return values.map((val: string) => ({ label: String(val), value: String(val) }));
      }
    } catch (err) {
      console.error("Failed to fetch Telemetry IDs", err);
    }
    return [];
  }
}
