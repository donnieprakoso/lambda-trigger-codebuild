#!/usr/bin/env node
import 'source-map-support/register';
import cdk = require('@aws-cdk/core');
import { LtcStack } from '../lib/ltc-stack';

const app = new cdk.App();
new LtcStack(app, 'LtcStack');
