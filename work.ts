import { DataQuery } from '@grafana/schema';

export interface MyQuery extends DataQuery {
  queryType: string; // 'panel' or 'variable'
  ticketId: string;
  telemetryId: string;
}

export const defaultQuery: Partial<MyQuery> = {
  queryType: 'panel',
  ticketId: '',
  telemetryId: '',
};

export interface MyVariableQuery {
  ticketId: string;
}

export interface MyDataSourceOptions {}









import { DataSourcePlugin } from '@grafana/data';
import { DataSource } from './datasource';
import { ConfigEditor } from './components/ConfigEditor';
import { QueryEditor } from './components/QueryEditor';
import { VariableQueryEditor } from './components/VariableQueryEditor';
import { MyQuery, MyDataSourceOptions } from './types';

export const plugin = new DataSourcePlugin<DataSource, MyQuery, MyDataSourceOptions>(DataSource)
  .setConfigEditor(ConfigEditor)
  .setQueryEditor(QueryEditor)
  .setVariableQueryEditor(VariableQueryEditor);
