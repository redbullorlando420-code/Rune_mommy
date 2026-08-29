import { C2S, S2C } from '/shared/protocol.js';
import { loadCatalog, item, recipes, items as itemTable } from '/shared/catalog.js';
import { NAME_RE, xpToLevel, INV_SIZE, BANK_SIZE } from '/shared/constants.js';
import { connect, send, on } from './net/client.js';
import { createRenderer } from './render.js';
import { openVN } from './vn.js';
